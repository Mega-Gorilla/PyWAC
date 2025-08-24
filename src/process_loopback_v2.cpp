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

#include <wrl/implements.h>
#include <wrl/client.h>

#include <vector>
#include <string>
#include <thread>
#include <atomic>
#include <mutex>
#include <condition_variable>
#include <iostream>
#include <iomanip>

using Microsoft::WRL::RuntimeClass;
using Microsoft::WRL::RuntimeClassFlags;
using Microsoft::WRL::ClassicCom;
using Microsoft::WRL::FtmBase;
using Microsoft::WRL::ComPtr;

namespace py = pybind11;

// Virtual audio device for process loopback
// This is defined in newer Windows SDK versions
#ifndef VIRTUAL_AUDIO_DEVICE_PROCESS_LOOPBACK
#define VIRTUAL_AUDIO_DEVICE_PROCESS_LOOPBACK L"VAD\\Process_Loopback"
#endif

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
        std::lock_guard<std::mutex> lock(mtx);
        
        // Get the activation result
        HRESULT hr = operation->GetActivateResult(&activateResult, 
                                                  reinterpret_cast<IUnknown**>(audioClient.GetAddressOf()));
        
        if (FAILED(hr)) {
            std::cerr << "GetActivateResult failed: 0x" << std::hex << hr << std::endl;
            activateResult = hr;
        } else if (FAILED(activateResult)) {
            std::cerr << "Activation failed: 0x" << std::hex << activateResult << std::endl;
        } else {
            std::cout << "Audio interface activated successfully!" << std::endl;
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

// Main process capture class
class ProcessCapture {
private:
    ComPtr<IAudioClient> audioClient;
    ComPtr<IAudioCaptureClient> captureClient;
    WAVEFORMATEX* waveFormat = nullptr;
    
    std::thread captureThread;
    std::atomic<bool> isCapturing{false};
    std::mutex bufferMutex;
    std::vector<float> audioBuffer;
    
    DWORD targetProcessId = 0;
    bool includeProcessTree = false;
    
    static constexpr UINT32 BUFFER_SIZE = 4800;  // 100ms at 48kHz
    
public:
    ProcessCapture() {
        HRESULT hr = CoInitializeEx(nullptr, COINIT_MULTITHREADED);
        if (FAILED(hr) && hr != RPC_E_CHANGED_MODE) {
            throw std::runtime_error("Failed to initialize COM");
        }
    }
    
    ~ProcessCapture() {
        Stop();
        if (waveFormat) {
            CoTaskMemFree(waveFormat);
        }
    }
    
    bool Start(DWORD processId, bool includeTree = false) {
        if (isCapturing) {
            std::cerr << "Already capturing" << std::endl;
            return false;
        }
        
        targetProcessId = processId;
        includeProcessTree = includeTree;
        
        std::cout << "Starting capture for PID: " << processId << std::endl;
        
        // Initialize audio client with process loopback
        HRESULT hr = InitializeProcessLoopback();
        if (FAILED(hr)) {
            std::cerr << "Failed to initialize process loopback: 0x" << std::hex << hr << std::endl;
            return false;
        }
        
        // Start capture thread
        isCapturing = true;
        captureThread = std::thread(&ProcessCapture::CaptureThreadFunc, this);
        
        std::cout << "Capture started successfully" << std::endl;
        return true;
    }
    
    void Stop() {
        if (isCapturing) {
            std::cout << "Stopping capture..." << std::endl;
            isCapturing = false;
            
            if (captureThread.joinable()) {
                captureThread.join();
            }
            
            if (audioClient) {
                audioClient->Stop();
            }
            
            std::cout << "Capture stopped" << std::endl;
        }
    }
    
    py::array_t<float> GetBuffer() {
        std::lock_guard<std::mutex> lock(bufferMutex);
        
        if (audioBuffer.empty()) {
            return py::array_t<float>(0);
        }
        
        auto result = py::array_t<float>(audioBuffer.size());
        auto ptr = static_cast<float*>(result.mutable_unchecked<1>().mutable_data(0));
        std::copy(audioBuffer.begin(), audioBuffer.end(), ptr);
        audioBuffer.clear();
        
        return result;
    }
    
    bool IsCapturing() const {
        return isCapturing;
    }
    
    static std::vector<ProcessInfo> ListAudioProcesses() {
        std::vector<ProcessInfo> processes;
        
        // For now, return active audio sessions
        // This could be enhanced to use IAudioSessionManager2
        
        CoInitializeEx(nullptr, COINIT_MULTITHREADED);
        
        ComPtr<IMMDeviceEnumerator> deviceEnumerator;
        HRESULT hr = CoCreateInstance(__uuidof(MMDeviceEnumerator), nullptr,
                                     CLSCTX_INPROC_SERVER, IID_PPV_ARGS(&deviceEnumerator));
        
        if (SUCCEEDED(hr)) {
            ComPtr<IMMDevice> device;
            hr = deviceEnumerator->GetDefaultAudioEndpoint(eRender, eConsole, &device);
            
            if (SUCCEEDED(hr)) {
                ComPtr<IAudioSessionManager2> sessionManager;
                hr = device->Activate(__uuidof(IAudioSessionManager2), CLSCTX_INPROC_SERVER,
                                     nullptr, reinterpret_cast<void**>(sessionManager.GetAddressOf()));
                
                if (SUCCEEDED(hr)) {
                    ComPtr<IAudioSessionEnumerator> sessionEnumerator;
                    hr = sessionManager->GetSessionEnumerator(&sessionEnumerator);
                    
                    if (SUCCEEDED(hr)) {
                        int sessionCount = 0;
                        sessionEnumerator->GetCount(&sessionCount);
                        
                        for (int i = 0; i < sessionCount; i++) {
                            ComPtr<IAudioSessionControl> sessionControl;
                            if (SUCCEEDED(sessionEnumerator->GetSession(i, &sessionControl))) {
                                ComPtr<IAudioSessionControl2> sessionControl2;
                                HRESULT hr2 = sessionControl.As(&sessionControl2);
                                
                                if (sessionControl2) {
                                    DWORD processId;
                                    if (SUCCEEDED(sessionControl2->GetProcessId(&processId)) && processId > 0) {
                                        // Get process name
                                        std::string processName = GetProcessName(processId);
                                        if (!processName.empty()) {
                                            processes.emplace_back(processId, processName);
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        
        CoUninitialize();
        return processes;
    }
    
private:
    HRESULT InitializeSystemLoopback() {
        std::cout << "Using system-wide loopback for PID 0" << std::endl;
        
        // Get default audio endpoint for loopback
        ComPtr<IMMDeviceEnumerator> deviceEnumerator;
        HRESULT hr = CoCreateInstance(__uuidof(MMDeviceEnumerator), nullptr,
                                     CLSCTX_INPROC_SERVER, IID_PPV_ARGS(&deviceEnumerator));
        if (FAILED(hr)) {
            std::cerr << "Failed to create device enumerator: 0x" << std::hex << hr << std::endl;
            return hr;
        }
        
        ComPtr<IMMDevice> device;
        hr = deviceEnumerator->GetDefaultAudioEndpoint(eRender, eConsole, &device);
        if (FAILED(hr)) {
            std::cerr << "Failed to get default audio endpoint: 0x" << std::hex << hr << std::endl;
            return hr;
        }
        
        // Activate audio client
        hr = device->Activate(__uuidof(IAudioClient), CLSCTX_INPROC_SERVER,
                             nullptr, reinterpret_cast<void**>(audioClient.GetAddressOf()));
        if (FAILED(hr)) {
            std::cerr << "Failed to activate audio client: 0x" << std::hex << hr << std::endl;
            return hr;
        }
        
        // Get mix format for system loopback
        hr = audioClient->GetMixFormat(&waveFormat);
        if (FAILED(hr)) {
            std::cerr << "GetMixFormat failed: 0x" << std::hex << hr << std::endl;
            return hr;
        }
        
        std::cout << "Audio format: " << waveFormat->nSamplesPerSec << "Hz, " 
                  << waveFormat->nChannels << " channels, "
                  << waveFormat->wBitsPerSample << " bits" << std::endl;
        
        // Initialize in loopback mode
        hr = audioClient->Initialize(
            AUDCLNT_SHAREMODE_SHARED,
            AUDCLNT_STREAMFLAGS_LOOPBACK,
            0,
            0,
            waveFormat,
            nullptr);
        
        if (FAILED(hr)) {
            std::cerr << "Initialize failed: 0x" << std::hex << hr << std::endl;
            return hr;
        }
        
        std::cout << "System loopback initialized" << std::endl;
        
        // Get capture client
        hr = audioClient->GetService(__uuidof(IAudioCaptureClient),
                                    reinterpret_cast<void**>(captureClient.GetAddressOf()));
        
        if (FAILED(hr)) {
            std::cerr << "GetService failed: 0x" << std::hex << hr << std::endl;
            return hr;
        }
        
        // Start audio client
        hr = audioClient->Start();
        if (FAILED(hr)) {
            std::cerr << "Start failed: 0x" << std::hex << hr << std::endl;
            return hr;
        }
        
        std::cout << "System loopback started" << std::endl;
        return S_OK;
    }
    
    HRESULT InitializeProcessLoopback() {
        std::cout << "Initializing loopback..." << std::endl;
        
        // If PID is 0, use regular system-wide loopback
        if (targetProcessId == 0) {
            return InitializeSystemLoopback();
        }
        
        // Setup activation parameters for process-specific loopback
        AUDIOCLIENT_ACTIVATION_PARAMS activationParams = {};
        activationParams.ActivationType = AUDIOCLIENT_ACTIVATION_TYPE_PROCESS_LOOPBACK;
        activationParams.ProcessLoopbackParams.TargetProcessId = targetProcessId;
        activationParams.ProcessLoopbackParams.ProcessLoopbackMode = includeProcessTree ?
            PROCESS_LOOPBACK_MODE_INCLUDE_TARGET_PROCESS_TREE :
            PROCESS_LOOPBACK_MODE_EXCLUDE_TARGET_PROCESS_TREE;
        
        std::cout << "Target PID: " << targetProcessId << std::endl;
        std::cout << "Include tree: " << (includeProcessTree ? "yes" : "no") << std::endl;
        
        // Create PROPVARIANT for activation
        PROPVARIANT propvariant = {};
        propvariant.vt = VT_BLOB;
        propvariant.blob.cbSize = sizeof(activationParams);
        propvariant.blob.pBlobData = reinterpret_cast<BYTE*>(&activationParams);
        
        // Create completion handler
        auto completionHandler = Microsoft::WRL::Make<CompletionHandler>();
        
        // Activate audio interface asynchronously
        ComPtr<IActivateAudioInterfaceAsyncOperation> asyncOp;
        HRESULT hr = ActivateAudioInterfaceAsync(
            VIRTUAL_AUDIO_DEVICE_PROCESS_LOOPBACK,
            __uuidof(IAudioClient),
            &propvariant,
            completionHandler.Get(),
            &asyncOp);
        
        if (FAILED(hr)) {
            std::cerr << "ActivateAudioInterfaceAsync failed: 0x" << std::hex << hr << std::endl;
            return hr;
        }
        
        std::cout << "Waiting for activation..." << std::endl;
        
        // Wait for completion
        completionHandler->Wait();
        
        if (FAILED(completionHandler->activateResult)) {
            std::cerr << "Activation failed with result: 0x" << std::hex 
                     << completionHandler->activateResult << std::endl;
            return completionHandler->activateResult;
        }
        
        audioClient = completionHandler->audioClient;
        if (!audioClient) {
            std::cerr << "No audio client obtained" << std::endl;
            return E_FAIL;
        }
        
        std::cout << "Audio client obtained successfully" << std::endl;
        
        // Process Loopback doesn't support GetMixFormat, use fixed format
        // According to Microsoft docs, use 48kHz, 2 channels, float32
        if (waveFormat) {
            CoTaskMemFree(waveFormat);
        }
        
        waveFormat = (WAVEFORMATEX*)CoTaskMemAlloc(sizeof(WAVEFORMATEX));
        if (!waveFormat) {
            return E_OUTOFMEMORY;
        }
        
        waveFormat->wFormatTag = WAVE_FORMAT_IEEE_FLOAT;
        waveFormat->nChannels = 2;
        waveFormat->nSamplesPerSec = 48000;
        waveFormat->wBitsPerSample = 32;
        waveFormat->nBlockAlign = waveFormat->nChannels * waveFormat->wBitsPerSample / 8;
        waveFormat->nAvgBytesPerSec = waveFormat->nSamplesPerSec * waveFormat->nBlockAlign;
        waveFormat->cbSize = 0;
        
        std::cout << "Using fixed audio format: " << waveFormat->nSamplesPerSec << "Hz, " 
                  << waveFormat->nChannels << " channels, "
                  << waveFormat->wBitsPerSample << " bits (float32)" << std::endl;
        
        // Initialize audio client
        hr = audioClient->Initialize(
            AUDCLNT_SHAREMODE_SHARED,
            AUDCLNT_STREAMFLAGS_LOOPBACK,
            0,
            0,
            waveFormat,
            nullptr);
        
        if (FAILED(hr)) {
            std::cerr << "Initialize failed: 0x" << std::hex << hr << std::endl;
            return hr;
        }
        
        std::cout << "Audio client initialized" << std::endl;
        
        // Get capture client
        hr = audioClient->GetService(__uuidof(IAudioCaptureClient),
                                    reinterpret_cast<void**>(captureClient.GetAddressOf()));
        
        if (FAILED(hr)) {
            std::cerr << "GetService failed: 0x" << std::hex << hr << std::endl;
            return hr;
        }
        
        std::cout << "Capture client obtained" << std::endl;
        
        // Start audio client
        hr = audioClient->Start();
        if (FAILED(hr)) {
            std::cerr << "Start failed: 0x" << std::hex << hr << std::endl;
            return hr;
        }
        
        std::cout << "Audio client started" << std::endl;
        
        return S_OK;
    }
    
    void CaptureThreadFunc() {
        std::cout << "Capture thread started" << std::endl;
        
        // Set thread priority for audio
        DWORD taskIndex = 0;
        HANDLE hTask = AvSetMmThreadCharacteristics(TEXT("Audio"), &taskIndex);
        
        while (isCapturing && captureClient) {
            BYTE* data = nullptr;
            UINT32 framesAvailable = 0;
            DWORD flags = 0;
            
            HRESULT hr = captureClient->GetBuffer(&data, &framesAvailable, &flags, nullptr, nullptr);
            
            if (SUCCEEDED(hr) && framesAvailable > 0) {
                // Convert to float samples
                std::vector<float> samples;
                
                if (waveFormat->wFormatTag == WAVE_FORMAT_IEEE_FLOAT) {
                    float* floatData = reinterpret_cast<float*>(data);
                    samples.assign(floatData, floatData + (framesAvailable * waveFormat->nChannels));
                } else if (waveFormat->wFormatTag == WAVE_FORMAT_PCM) {
                    if (waveFormat->wBitsPerSample == 16) {
                        int16_t* int16Data = reinterpret_cast<int16_t*>(data);
                        samples.reserve(framesAvailable * waveFormat->nChannels);
                        for (UINT32 i = 0; i < framesAvailable * waveFormat->nChannels; ++i) {
                            samples.push_back(int16Data[i] / 32768.0f);
                        }
                    } else if (waveFormat->wBitsPerSample == 32) {
                        int32_t* int32Data = reinterpret_cast<int32_t*>(data);
                        samples.reserve(framesAvailable * waveFormat->nChannels);
                        for (UINT32 i = 0; i < framesAvailable * waveFormat->nChannels; ++i) {
                            samples.push_back(int32Data[i] / 2147483648.0f);
                        }
                    }
                }
                
                // Add to buffer
                if (!samples.empty()) {
                    std::lock_guard<std::mutex> lock(bufferMutex);
                    audioBuffer.insert(audioBuffer.end(), samples.begin(), samples.end());
                    
                    // Limit buffer size
                    if (audioBuffer.size() > BUFFER_SIZE * 10) {
                        audioBuffer.erase(audioBuffer.begin(), 
                                        audioBuffer.begin() + audioBuffer.size() - BUFFER_SIZE * 10);
                    }
                }
                
                captureClient->ReleaseBuffer(framesAvailable);
            } else if (hr == AUDCLNT_S_BUFFER_EMPTY) {
                // No data available, sleep briefly
                Sleep(10);
            } else if (FAILED(hr)) {
                std::cerr << "GetBuffer failed: 0x" << std::hex << hr << std::endl;
                break;
            }
        }
        
        if (hTask) {
            AvRevertMmThreadCharacteristics(hTask);
        }
        
        std::cout << "Capture thread ended" << std::endl;
    }
    
    static std::string GetProcessName(DWORD processId) {
        std::string processName;
        
        HANDLE hProcess = OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, FALSE, processId);
        if (hProcess) {
            char buffer[MAX_PATH];
            DWORD bufferSize = MAX_PATH;
            if (QueryFullProcessImageNameA(hProcess, 0, buffer, &bufferSize)) {
                std::string fullPath(buffer);
                size_t lastSlash = fullPath.find_last_of("\\/");
                if (lastSlash != std::string::npos) {
                    processName = fullPath.substr(lastSlash + 1);
                }
            }
            CloseHandle(hProcess);
        }
        
        return processName;
    }
};

// Python bindings
PYBIND11_MODULE(process_loopback_v2, m) {
    m.doc() = "Process-specific audio loopback capture for Windows (v2)";
    
    py::class_<ProcessInfo>(m, "ProcessInfo")
        .def_readonly("pid", &ProcessInfo::pid)
        .def_readonly("name", &ProcessInfo::name)
        .def("__repr__", [](const ProcessInfo& p) {
            return "<ProcessInfo pid=" + std::to_string(p.pid) + " name='" + p.name + "'>";
        });
    
    py::class_<ProcessCapture>(m, "ProcessCapture")
        .def(py::init<>())
        .def("start", &ProcessCapture::Start, 
             py::arg("process_id"), 
             py::arg("include_tree") = false,
             "Start capturing audio from specified process")
        .def("stop", &ProcessCapture::Stop, "Stop audio capture")
        .def("get_buffer", &ProcessCapture::GetBuffer, "Get captured audio buffer as numpy array")
        .def("is_capturing", &ProcessCapture::IsCapturing, "Check if currently capturing")
        .def_static("list_audio_processes", &ProcessCapture::ListAudioProcesses, 
                   "List processes with audio sessions");
    
    m.def("list_audio_processes", &ProcessCapture::ListAudioProcesses, 
          "List processes with audio sessions");
}