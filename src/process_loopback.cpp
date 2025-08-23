#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include <windows.h>
#include <mmdeviceapi.h>
#include <audioclient.h>
#include <audiopolicy.h>
#include <functiondiscoverykeys_devpkey.h>
#include <mmdeviceapi.h>
#include <audioenginebaseapo.h>
#include <vector>
#include <string>
#include <thread>
#include <atomic>
#include <mutex>
#include <condition_variable>
#include <comdef.h>
#include <psapi.h>
#include <tlhelp32.h>
#include <wrl/client.h>
#include <memory>

// Process Loopback API definitions (Windows 10 2004+)
#ifndef AUDIOCLIENT_ACTIVATION_TYPE_PROCESS_LOOPBACK
#define AUDIOCLIENT_ACTIVATION_TYPE_PROCESS_LOOPBACK 0x00000001
#endif

#ifndef PROCESS_LOOPBACK_MODE_INCLUDE_TARGET_PROCESS_TREE
enum PROCESS_LOOPBACK_MODE {
    PROCESS_LOOPBACK_MODE_INCLUDE_TARGET_PROCESS_TREE = 0,
    PROCESS_LOOPBACK_MODE_EXCLUDE_TARGET_PROCESS_TREE = 1
};
#endif

struct AUDIOCLIENT_PROCESS_LOOPBACK_PARAMS {
    DWORD TargetProcessId;
    PROCESS_LOOPBACK_MODE ProcessLoopbackMode;
};

// Forward declarations for ActivateAudioInterfaceAsync
struct __declspec(uuid("72A22D78-CDE4-431D-B8CC-843A71199B6D")) IActivateAudioInterfaceAsyncOperation;
struct __declspec(uuid("41D949AB-9862-444A-80F6-C261334DA5EB")) IActivateAudioInterfaceCompletionHandler;

typedef HRESULT(WINAPI* ActivateAudioInterfaceAsync_t)(
    LPCWSTR deviceInterfacePath,
    REFIID riid,
    PROPVARIANT* activationParams,
    IActivateAudioInterfaceCompletionHandler* completionHandler,
    IActivateAudioInterfaceAsyncOperation** activationOperation
);

using Microsoft::WRL::ComPtr;

namespace py = pybind11;

class ProcessInfo {
public:
    DWORD pid;
    std::wstring name;
    
    ProcessInfo(DWORD p, const std::wstring& n) : pid(p), name(n) {}
};

class ProcessLoopbackCapture {
private:
    IAudioClient* audioClient = nullptr;
    IAudioCaptureClient* captureClient = nullptr;
    WAVEFORMATEX* waveFormat = nullptr;
    std::thread captureThread;
    std::atomic<bool> isCapturing{false};
    std::mutex bufferMutex;
    std::vector<float> audioBuffer;
    DWORD targetProcessId = 0;
    
    static constexpr UINT32 BUFFER_SIZE = 4096;
    
public:
    ProcessLoopbackCapture() {
        HRESULT hr = CoInitializeEx(nullptr, COINIT_APARTMENTTHREADED);
        if (FAILED(hr) && hr != RPC_E_CHANGED_MODE) {
            throw std::runtime_error("Failed to initialize COM");
        }
    }
    
    ~ProcessLoopbackCapture() {
        StopCapture();
        if (captureClient) captureClient->Release();
        if (audioClient) audioClient->Release();
        if (waveFormat) CoTaskMemFree(waveFormat);
        CoUninitialize();
    }
    
    bool StartCapture(DWORD processId) {
        if (isCapturing) {
            return false;
        }
        
        targetProcessId = processId;
        
        // Initialize audio client for loopback capture
        HRESULT hr = InitializeAudioClient();
        if (FAILED(hr)) {
            return false;
        }
        
        // Start capture thread
        isCapturing = true;
        captureThread = std::thread(&ProcessLoopbackCapture::CaptureThreadFunc, this);
        
        return true;
    }
    
    void StopCapture() {
        if (isCapturing) {
            isCapturing = false;
            if (captureThread.joinable()) {
                captureThread.join();
            }
        }
    }
    
    py::array_t<float> GetAudioBuffer() {
        std::lock_guard<std::mutex> lock(bufferMutex);
        auto result = py::array_t<float>(audioBuffer.size());
        auto ptr = static_cast<float*>(result.mutable_unchecked<1>().mutable_data(0));
        std::copy(audioBuffer.begin(), audioBuffer.end(), ptr);
        audioBuffer.clear();
        return result;
    }
    
    static std::vector<ProcessInfo> GetAudioProcesses() {
        std::vector<ProcessInfo> processes;
        
        HANDLE snapshot = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
        if (snapshot == INVALID_HANDLE_VALUE) {
            return processes;
        }
        
        PROCESSENTRY32W pe32;
        pe32.dwSize = sizeof(PROCESSENTRY32W);
        
        if (Process32FirstW(snapshot, &pe32)) {
            do {
                // Filter common audio-producing processes
                std::wstring processName(pe32.szExeFile);
                if (processName.find(L"chrome.exe") != std::wstring::npos ||
                    processName.find(L"firefox.exe") != std::wstring::npos ||
                    processName.find(L"spotify.exe") != std::wstring::npos ||
                    processName.find(L"discord.exe") != std::wstring::npos ||
                    processName.find(L"vlc.exe") != std::wstring::npos ||
                    processName.find(L"wmplayer.exe") != std::wstring::npos) {
                    processes.emplace_back(pe32.th32ProcessID, processName);
                }
            } while (Process32NextW(snapshot, &pe32));
        }
        
        CloseHandle(snapshot);
        return processes;
    }
    
private:
    HRESULT InitializeAudioClient() {
        // Get default audio device
        IMMDeviceEnumerator* deviceEnumerator = nullptr;
        IMMDevice* device = nullptr;
        
        HRESULT hr = CoCreateInstance(
            __uuidof(MMDeviceEnumerator),
            nullptr,
            CLSCTX_ALL,
            __uuidof(IMMDeviceEnumerator),
            (void**)&deviceEnumerator
        );
        
        if (FAILED(hr)) return hr;
        
        hr = deviceEnumerator->GetDefaultAudioEndpoint(
            eRender,
            eConsole,
            &device
        );
        
        deviceEnumerator->Release();
        if (FAILED(hr)) return hr;
        
        // Activate audio client
        hr = device->Activate(
            __uuidof(IAudioClient),
            CLSCTX_ALL,
            nullptr,
            (void**)&audioClient
        );
        
        device->Release();
        if (FAILED(hr)) return hr;
        
        // Get mix format
        hr = audioClient->GetMixFormat(&waveFormat);
        if (FAILED(hr)) return hr;
        
        // Initialize in loopback mode
        hr = audioClient->Initialize(
            AUDCLNT_SHAREMODE_SHARED,
            AUDCLNT_STREAMFLAGS_LOOPBACK,
            0,
            0,
            waveFormat,
            nullptr
        );
        
        if (FAILED(hr)) return hr;
        
        // Get capture client
        hr = audioClient->GetService(
            __uuidof(IAudioCaptureClient),
            (void**)&captureClient
        );
        
        return hr;
    }
    
    void CaptureThreadFunc() {
        if (!audioClient || !captureClient) return;
        
        HRESULT hr = audioClient->Start();
        if (FAILED(hr)) return;
        
        while (isCapturing) {
            UINT32 packetLength = 0;
            hr = captureClient->GetNextPacketSize(&packetLength);
            
            if (SUCCEEDED(hr) && packetLength > 0) {
                BYTE* data = nullptr;
                UINT32 numFramesAvailable;
                DWORD flags;
                
                hr = captureClient->GetBuffer(
                    &data,
                    &numFramesAvailable,
                    &flags,
                    nullptr,
                    nullptr
                );
                
                if (SUCCEEDED(hr)) {
                    // Convert to float and store
                    std::lock_guard<std::mutex> lock(bufferMutex);
                    
                    if (waveFormat->wFormatTag == WAVE_FORMAT_IEEE_FLOAT) {
                        float* floatData = reinterpret_cast<float*>(data);
                        audioBuffer.insert(audioBuffer.end(), 
                            floatData, 
                            floatData + (numFramesAvailable * waveFormat->nChannels));
                    } else if (waveFormat->wFormatTag == WAVE_FORMAT_PCM) {
                        // Convert PCM to float
                        int16_t* pcmData = reinterpret_cast<int16_t*>(data);
                        for (UINT32 i = 0; i < numFramesAvailable * waveFormat->nChannels; i++) {
                            audioBuffer.push_back(pcmData[i] / 32768.0f);
                        }
                    }
                    
                    captureClient->ReleaseBuffer(numFramesAvailable);
                }
            }
            
            std::this_thread::sleep_for(std::chrono::milliseconds(10));
        }
        
        audioClient->Stop();
    }
};

PYBIND11_MODULE(process_loopback, m) {
    m.doc() = "Process-specific audio loopback capture for Windows";
    
    py::class_<ProcessInfo>(m, "ProcessInfo")
        .def_readonly("pid", &ProcessInfo::pid)
        .def_property_readonly("name", [](const ProcessInfo& p) {
            return py::str(std::string(p.name.begin(), p.name.end()));
        });
    
    py::class_<ProcessLoopbackCapture>(m, "ProcessCapture")
        .def(py::init<>())
        .def("start", &ProcessLoopbackCapture::StartCapture, 
             "Start capturing audio from specified process",
             py::arg("pid"))
        .def("stop", &ProcessLoopbackCapture::StopCapture,
             "Stop audio capture")
        .def("get_buffer", &ProcessLoopbackCapture::GetAudioBuffer,
             "Get captured audio buffer as numpy array");
    
    m.def("list_audio_processes", []() {
        auto processes = ProcessLoopbackCapture::GetAudioProcesses();
        py::list result;
        for (const auto& proc : processes) {
            py::dict d;
            d["pid"] = proc.pid;
            d["name"] = py::str(std::string(proc.name.begin(), proc.name.end()));
            result.append(d);
        }
        return result;
    }, "List processes that commonly produce audio");
}