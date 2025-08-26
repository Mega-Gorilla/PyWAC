/**
 * Queue-based Process Audio Capture Implementation
 * 
 * This implementation uses a thread-safe queue to avoid GIL issues
 * when transferring audio data from C++ capture thread to Python.
 */

#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>

#include <windows.h>
#include <mmdeviceapi.h>
#include <audioclient.h>
#include <audioclientactivationparams.h>
#include <audiopolicy.h>
#include <avrt.h>
#include <combaseapi.h>
#include <psapi.h>

#include <wrl/implements.h>
#include <wrl/client.h>

#include <vector>
#include <queue>
#include <string>
#include <thread>
#include <atomic>
#include <mutex>
#include <condition_variable>
#include <iostream>
#include <iomanip>
#include <chrono>
#include <memory>

using Microsoft::WRL::RuntimeClass;
using Microsoft::WRL::RuntimeClassFlags;
using Microsoft::WRL::ClassicCom;
using Microsoft::WRL::FtmBase;
using Microsoft::WRL::ComPtr;

namespace py = pybind11;

// Virtual audio device for process loopback
#ifndef VIRTUAL_AUDIO_DEVICE_PROCESS_LOOPBACK
#define VIRTUAL_AUDIO_DEVICE_PROCESS_LOOPBACK L"VAD\\Process_Loopback"
#endif

// Buffer flags
#ifndef AUDCLNT_BUFFERFLAGS_SILENT
#define AUDCLNT_BUFFERFLAGS_SILENT 0x2
#endif

// Audio chunk structure
struct AudioChunk {
    std::vector<float> data;
    size_t frameCount;
    bool silent;
    std::chrono::steady_clock::time_point timestamp;
    
    AudioChunk() : frameCount(0), silent(false) {}
    AudioChunk(size_t frames) : data(frames * 2), frameCount(frames), silent(false) {
        timestamp = std::chrono::steady_clock::now();
    }
};

// Thread-safe audio queue implementation
class ThreadSafeAudioQueue {
private:
    std::queue<AudioChunk> queue;
    mutable std::mutex mutex;
    std::condition_variable cv;
    
    size_t maxSize;
    size_t totalChunks = 0;
    size_t droppedChunks = 0;
    std::atomic<bool> closed{false};
    
public:
    ThreadSafeAudioQueue(size_t max_size = 1000) : maxSize(max_size) {}
    
    // Producer side - called from C++ capture thread
    bool push(AudioChunk&& chunk) {
        std::unique_lock<std::mutex> lock(mutex);
        
        if (closed) return false;
        
        // Drop oldest if queue is full
        if (queue.size() >= maxSize) {
            queue.pop();
            droppedChunks++;
        }
        
        queue.push(std::move(chunk));
        totalChunks++;
        
        cv.notify_one();
        return true;
    }
    
    // Consumer side - called from Python
    std::vector<AudioChunk> popBatch(size_t maxChunks = 10, int timeoutMs = 10) {
        std::unique_lock<std::mutex> lock(mutex);
        std::vector<AudioChunk> result;
        
        // Wait for data or timeout
        auto deadline = std::chrono::steady_clock::now() + std::chrono::milliseconds(timeoutMs);
        cv.wait_until(lock, deadline, [this] { return !queue.empty() || closed; });
        
        // Collect up to maxChunks
        while (!queue.empty() && result.size() < maxChunks) {
            result.push_back(std::move(queue.front()));
            queue.pop();
        }
        
        return result;
    }
    
    // Get single chunk (for compatibility)
    std::unique_ptr<AudioChunk> pop(int timeoutMs = 10) {
        auto batch = popBatch(1, timeoutMs);
        if (batch.empty()) {
            return nullptr;
        }
        return std::make_unique<AudioChunk>(std::move(batch[0]));
    }
    
    void clear() {
        std::unique_lock<std::mutex> lock(mutex);
        std::queue<AudioChunk> empty;
        std::swap(queue, empty);
    }
    
    size_t size() const {
        std::unique_lock<std::mutex> lock(mutex);
        return queue.size();
    }
    
    bool empty() const {
        std::unique_lock<std::mutex> lock(mutex);
        return queue.empty();
    }
    
    void close() {
        std::unique_lock<std::mutex> lock(mutex);
        closed = true;
        cv.notify_all();
    }
    
    std::map<std::string, size_t> getStats() const {
        std::unique_lock<std::mutex> lock(mutex);
        return {
            {"queue_size", queue.size()},
            {"total_chunks", totalChunks},
            {"dropped_chunks", droppedChunks}
        };
    }
};

// Process information class
class ProcessInfo {
public:
    DWORD pid;
    std::string name;
    
    ProcessInfo(DWORD p, const std::string& n) : pid(p), name(n) {}
};

// Completion handler for async audio interface activation
class CompletionHandler : public RuntimeClass<RuntimeClassFlags<ClassicCom>, FtmBase, 
                                             IActivateAudioInterfaceCompletionHandler> {
public:
    ComPtr<IAudioClient> audioClient;
    HRESULT activateResult = E_FAIL;
    std::condition_variable cv;
    std::mutex mtx;
    bool completed = false;

    STDMETHOD(ActivateCompleted)(IActivateAudioInterfaceAsyncOperation* operation) override {
        std::unique_lock<std::mutex> lock(mtx);
        
        // Get the activation result
        HRESULT hr = operation->GetActivateResult(&activateResult, 
                                                  reinterpret_cast<IUnknown**>(audioClient.GetAddressOf()));
        
        if (FAILED(hr)) {
            std::cerr << "GetActivateResult failed: 0x" << std::hex << hr << std::endl;
            activateResult = hr;
        } else if (FAILED(activateResult)) {
            std::cerr << "Activation failed: 0x" << std::hex << activateResult << std::endl;
        }
        
        completed = true;
        cv.notify_all();
        
        return S_OK;
    }
    
    void Wait() {
        std::unique_lock<std::mutex> lock(mtx);
        cv.wait(lock, [this] { return completed; });
    }
};

// Queue-based process capture class
class QueueBasedProcessCapture {
private:
    ComPtr<IAudioClient> audioClient;
    ComPtr<IAudioCaptureClient> captureClient;
    WAVEFORMATEX* waveFormat = nullptr;
    
    std::thread captureThread;
    std::atomic<bool> capturing{false};
    std::atomic<bool> shouldStop{false};
    
    ThreadSafeAudioQueue audioQueue;
    size_t chunkSize = 480;  // 10ms at 48kHz
    
    // Performance metrics
    std::atomic<size_t> totalFramesCaptured{0};
    std::atomic<size_t> totalSilentFrames{0};
    std::atomic<size_t> captureErrors{0};
    std::chrono::steady_clock::time_point startTime;
    
    void captureLoop() {
        // Set thread priority for audio
        DWORD taskIndex = 0;
        HANDLE hTask = AvSetMmThreadCharacteristics(TEXT("Audio"), &taskIndex);
        
        if (hTask == NULL) {
            std::cerr << "Warning: Could not set thread characteristics" << std::endl;
        }
        
        HRESULT hr = audioClient->Start();
        if (FAILED(hr)) {
            std::cerr << "Failed to start audio client: 0x" << std::hex << hr << std::endl;
            captureErrors++;
            if (hTask) AvRevertMmThreadCharacteristics(hTask);
            return;
        }
        
        std::cout << "Capture thread started, chunk size: " << chunkSize << " frames" << std::endl;
        
        // Accumulator for partial chunks
        AudioChunk currentChunk(chunkSize);
        size_t currentOffset = 0;
        
        while (!shouldStop) {
            UINT32 packetSize = 0;
            hr = captureClient->GetNextPacketSize(&packetSize);
            
            if (FAILED(hr)) {
                captureErrors++;
                std::this_thread::sleep_for(std::chrono::milliseconds(1));
                continue;
            }
            
            while (packetSize != 0 && !shouldStop) {
                BYTE* pData = nullptr;
                UINT32 framesAvailable = 0;
                DWORD flags = 0;
                
                hr = captureClient->GetBuffer(&pData, &framesAvailable, &flags, nullptr, nullptr);
                
                if (SUCCEEDED(hr)) {
                    bool isSilent = (flags & AUDCLNT_BUFFERFLAGS_SILENT) != 0;
                    
                    if (isSilent) {
                        totalSilentFrames += framesAvailable;
                    }
                    
                    // Process frames into chunks
                    float* floatData = reinterpret_cast<float*>(pData);
                    size_t framesToProcess = framesAvailable;
                    size_t sourceOffset = 0;
                    
                    while (framesToProcess > 0) {
                        size_t framesToCopy = (framesToProcess < (chunkSize - currentOffset)) ? framesToProcess : (chunkSize - currentOffset);
                        
                        if (!isSilent && floatData) {
                            // Copy actual audio data
                            std::memcpy(
                                currentChunk.data.data() + currentOffset * 2,
                                floatData + sourceOffset * 2,
                                framesToCopy * 2 * sizeof(float)
                            );
                        } else {
                            // Fill with silence
                            std::memset(
                                currentChunk.data.data() + currentOffset * 2,
                                0,
                                framesToCopy * 2 * sizeof(float)
                            );
                        }
                        
                        currentOffset += framesToCopy;
                        sourceOffset += framesToCopy;
                        framesToProcess -= framesToCopy;
                        
                        // If chunk is full, push to queue
                        if (currentOffset >= chunkSize) {
                            currentChunk.silent = isSilent;
                            audioQueue.push(std::move(currentChunk));
                            
                            // Prepare new chunk
                            currentChunk = AudioChunk(chunkSize);
                            currentOffset = 0;
                        }
                    }
                    
                    totalFramesCaptured += framesAvailable;
                    
                    hr = captureClient->ReleaseBuffer(framesAvailable);
                    if (FAILED(hr)) {
                        captureErrors++;
                    }
                } else {
                    captureErrors++;
                }
                
                hr = captureClient->GetNextPacketSize(&packetSize);
                if (FAILED(hr)) {
                    captureErrors++;
                    break;
                }
            }
            
            // Small sleep to prevent CPU spinning
            std::this_thread::sleep_for(std::chrono::milliseconds(1));
        }
        
        // Push any remaining partial chunk
        if (currentOffset > 0) {
            currentChunk.frameCount = currentOffset;
            currentChunk.data.resize(currentOffset * 2);
            audioQueue.push(std::move(currentChunk));
        }
        
        audioClient->Stop();
        
        if (hTask) {
            AvRevertMmThreadCharacteristics(hTask);
        }
        
        std::cout << "Capture thread stopped" << std::endl;
    }
    
public:
    QueueBasedProcessCapture(size_t queueSize = 1000) : audioQueue(queueSize) {}
    
    ~QueueBasedProcessCapture() {
        stop();
        if (waveFormat) {
            CoTaskMemFree(waveFormat);
        }
    }
    
    bool start(DWORD processId) {
        if (capturing.load()) {
            std::cerr << "Already capturing" << std::endl;
            return false;
        }
        
        HRESULT hr = CoInitializeEx(nullptr, COINIT_MULTITHREADED);
        bool needsUninit = SUCCEEDED(hr);
        
        std::cout << "Starting capture for PID: " << processId << std::endl;
        
        // Create activation parameters
        AUDIOCLIENT_ACTIVATION_PARAMS activationParams = {};
        activationParams.ActivationType = AUDIOCLIENT_ACTIVATION_TYPE_PROCESS_LOOPBACK;
        activationParams.ProcessLoopbackParams.ProcessLoopbackMode = PROCESS_LOOPBACK_MODE_INCLUDE_TARGET_PROCESS_TREE;
        activationParams.ProcessLoopbackParams.TargetProcessId = processId;
        
        PROPVARIANT activateParams = {};
        activateParams.vt = VT_BLOB;
        activateParams.blob.cbSize = sizeof(activationParams);
        activateParams.blob.pBlobData = reinterpret_cast<BYTE*>(&activationParams);
        
        // Create completion handler
        ComPtr<CompletionHandler> completionHandler;
        completionHandler = Microsoft::WRL::Make<CompletionHandler>();
        
        // Activate audio interface asynchronously
        ComPtr<IActivateAudioInterfaceAsyncOperation> asyncOp;
        hr = ActivateAudioInterfaceAsync(
            VIRTUAL_AUDIO_DEVICE_PROCESS_LOOPBACK,
            __uuidof(IAudioClient),
            &activateParams,
            completionHandler.Get(),
            &asyncOp
        );
        
        if (FAILED(hr)) {
            std::cerr << "ActivateAudioInterfaceAsync failed: 0x" << std::hex << hr << std::endl;
            if (needsUninit) CoUninitialize();
            return false;
        }
        
        // Wait for completion
        completionHandler->Wait();
        
        if (FAILED(completionHandler->activateResult)) {
            std::cerr << "Audio activation failed: 0x" << std::hex << completionHandler->activateResult << std::endl;
            if (needsUninit) CoUninitialize();
            return false;
        }
        
        audioClient = completionHandler->audioClient;
        
        // Use fixed format for Process Loopback
        WAVEFORMATEX format = {};
        format.wFormatTag = WAVE_FORMAT_IEEE_FLOAT;
        format.nChannels = 2;
        format.nSamplesPerSec = 48000;
        format.wBitsPerSample = 32;
        format.nBlockAlign = format.nChannels * format.wBitsPerSample / 8;
        format.nAvgBytesPerSec = format.nSamplesPerSec * format.nBlockAlign;
        format.cbSize = 0;
        
        // Initialize with fixed format
        hr = audioClient->Initialize(
            AUDCLNT_SHAREMODE_SHARED,
            AUDCLNT_STREAMFLAGS_LOOPBACK,
            0, 0,
            &format,
            nullptr
        );
        
        if (FAILED(hr)) {
            std::cerr << "Initialize failed: 0x" << std::hex << hr << std::endl;
            if (needsUninit) CoUninitialize();
            return false;
        }
        
        // Store format
        waveFormat = reinterpret_cast<WAVEFORMATEX*>(CoTaskMemAlloc(sizeof(WAVEFORMATEX)));
        if (waveFormat) {
            memcpy(waveFormat, &format, sizeof(WAVEFORMATEX));
        }
        
        // Get capture client
        hr = audioClient->GetService(__uuidof(IAudioCaptureClient),
                                    reinterpret_cast<void**>(captureClient.GetAddressOf()));
        if (FAILED(hr)) {
            std::cerr << "GetService failed: 0x" << std::hex << hr << std::endl;
            if (needsUninit) CoUninitialize();
            return false;
        }
        
        // Clear queue and reset metrics
        audioQueue.clear();
        totalFramesCaptured = 0;
        totalSilentFrames = 0;
        captureErrors = 0;
        startTime = std::chrono::steady_clock::now();
        
        // Start capture thread
        shouldStop = false;
        capturing = true;
        captureThread = std::thread(&QueueBasedProcessCapture::captureLoop, this);
        
        std::cout << "Capture started successfully!" << std::endl;
        return true;
    }
    
    void stop() {
        if (!capturing.load()) {
            return;
        }
        
        shouldStop = true;
        audioQueue.close();
        
        if (captureThread.joinable()) {
            captureThread.join();
        }
        
        capturing = false;
        
        // Release COM objects
        captureClient.Reset();
        audioClient.Reset();
    }
    
    void setChunkSize(size_t frames) {
        if (!capturing.load()) {
            chunkSize = frames;
            std::cout << "Chunk size set to " << frames << " frames" << std::endl;
        }
    }
    
    // Python interface methods
    py::list popChunks(size_t maxChunks = 10, int timeoutMs = 10) {
        py::list result;
        
        auto chunks = audioQueue.popBatch(maxChunks, timeoutMs);
        
        for (auto& chunk : chunks) {
            // Create numpy array from chunk data
            py::array_t<float> arr({static_cast<py::ssize_t>(chunk.frameCount), static_cast<py::ssize_t>(2)});
            auto ptr = static_cast<float*>(arr.mutable_unchecked<2>().mutable_data(0, 0));
            std::memcpy(ptr, chunk.data.data(), chunk.frameCount * 2 * sizeof(float));
            
            // Create dictionary with chunk metadata
            py::dict chunkDict;
            chunkDict["data"] = arr;
            chunkDict["silent"] = chunk.silent;
            chunkDict["timestamp"] = std::chrono::duration_cast<std::chrono::microseconds>(
                chunk.timestamp.time_since_epoch()).count();
            
            result.append(chunkDict);
        }
        
        return result;
    }
    
    py::object popChunk(int timeoutMs = 10) {
        auto chunk = audioQueue.pop(timeoutMs);
        
        if (!chunk) {
            return py::none();
        }
        
        // Create numpy array
        py::array_t<float> arr({static_cast<py::ssize_t>(chunk->frameCount), static_cast<py::ssize_t>(2)});
        auto ptr = static_cast<float*>(arr.mutable_unchecked<2>().mutable_data(0, 0));
        std::memcpy(ptr, chunk->data.data(), chunk->frameCount * 2 * sizeof(float));
        
        // Create dictionary with chunk metadata
        py::dict chunkDict;
        chunkDict["data"] = arr;
        chunkDict["silent"] = chunk->silent;
        chunkDict["timestamp"] = std::chrono::duration_cast<std::chrono::microseconds>(
            chunk->timestamp.time_since_epoch()).count();
        
        return chunkDict;
    }
    
    size_t queueSize() const {
        return audioQueue.size();
    }
    
    bool isCapturing() const {
        return capturing.load();
    }
    
    py::dict getMetrics() const {
        auto now = std::chrono::steady_clock::now();
        double elapsed = std::chrono::duration<double>(now - startTime).count();
        
        auto queueStats = audioQueue.getStats();
        
        py::dict metrics;
        metrics["capturing"] = capturing.load();
        metrics["total_frames"] = totalFramesCaptured.load();
        metrics["total_silent_frames"] = totalSilentFrames.load();
        metrics["capture_errors"] = captureErrors.load();
        metrics["elapsed_seconds"] = elapsed;
        metrics["queue_size"] = queueStats["queue_size"];
        metrics["total_chunks"] = queueStats["total_chunks"];
        metrics["dropped_chunks"] = queueStats["dropped_chunks"];
        metrics["chunk_size"] = chunkSize;
        
        if (elapsed > 0) {
            metrics["frames_per_second"] = totalFramesCaptured.load() / elapsed;
        }
        
        return metrics;
    }
};

// Helper function to list audio processes
std::vector<ProcessInfo> listAudioProcesses() {
    std::vector<ProcessInfo> processes;
    
    // Get all process IDs
    DWORD processIds[1024];
    DWORD bytesReturned;
    
    if (EnumProcesses(processIds, sizeof(processIds), &bytesReturned)) {
        DWORD processCount = bytesReturned / sizeof(DWORD);
        
        for (DWORD i = 0; i < processCount; i++) {
            if (processIds[i] != 0) {
                HANDLE hProcess = OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, FALSE, processIds[i]);
                
                if (hProcess) {
                    char processName[MAX_PATH] = "";
                    HMODULE hMod;
                    DWORD cbNeeded;
                    
                    if (EnumProcessModules(hProcess, &hMod, sizeof(hMod), &cbNeeded)) {
                        GetModuleBaseNameA(hProcess, hMod, processName, sizeof(processName));
                        
                        // Filter common audio-producing processes
                        std::string name(processName);
                        if (!name.empty() && name != "System" && name != "Registry") {
                            processes.emplace_back(processIds[i], name);
                        }
                    }
                    
                    CloseHandle(hProcess);
                }
            }
        }
    }
    
    return processes;
}

// Python module definition
PYBIND11_MODULE(process_loopback_queue, m) {
    m.doc() = "Queue-based Process Audio Capture Module";
    
    // Process Info class
    py::class_<ProcessInfo>(m, "ProcessInfo")
        .def_readonly("pid", &ProcessInfo::pid)
        .def_readonly("name", &ProcessInfo::name)
        .def("__repr__", [](const ProcessInfo& p) {
            return "<ProcessInfo pid=" + std::to_string(p.pid) + " name='" + p.name + "'>";
        });
    
    // Queue-based capture class
    py::class_<QueueBasedProcessCapture>(m, "QueueBasedProcessCapture")
        .def(py::init<size_t>(), py::arg("queue_size") = 1000)
        .def("start", &QueueBasedProcessCapture::start, py::arg("process_id"),
             "Start capturing audio from the specified process")
        .def("stop", &QueueBasedProcessCapture::stop,
             "Stop audio capture")
        .def("set_chunk_size", &QueueBasedProcessCapture::setChunkSize, py::arg("frames"),
             "Set the chunk size in frames (must be called before start)")
        .def("pop_chunks", &QueueBasedProcessCapture::popChunks, 
             py::arg("max_chunks") = 10, py::arg("timeout_ms") = 10,
             "Pop multiple chunks from the queue")
        .def("pop_chunk", &QueueBasedProcessCapture::popChunk,
             py::arg("timeout_ms") = 10,
             "Pop a single chunk from the queue")
        .def("queue_size", &QueueBasedProcessCapture::queueSize,
             "Get current queue size")
        .def("is_capturing", &QueueBasedProcessCapture::isCapturing,
             "Check if capture is active")
        .def("get_metrics", &QueueBasedProcessCapture::getMetrics,
             "Get performance metrics");
    
    // Module functions
    m.def("list_audio_processes", &listAudioProcesses,
          "List all processes that might produce audio");
}