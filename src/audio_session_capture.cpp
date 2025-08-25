#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include <windows.h>
#include <mmdeviceapi.h>
#include <audioclient.h>
#include <audiopolicy.h>
#include <endpointvolume.h>
#include <functiondiscoverykeys_devpkey.h>
#include <wrl/client.h>
#include <vector>
#include <string>
#include <map>
#include <mutex>
#include <memory>
#include <psapi.h>
#include <tlhelp32.h>

#pragma comment(lib, "ole32.lib")
#pragma comment(lib, "uuid.lib")
#pragma comment(lib, "psapi.lib")

namespace py = pybind11;
using namespace Microsoft::WRL;

// Structure to hold session information
struct AudioSessionInfo {
    DWORD processId;
    std::wstring sessionId;
    std::string processName;
    std::string displayName;
    AudioSessionState state;
    float volume;
    bool muted;
};

class AudioSessionEnumerator {
private:
    ComPtr<IMMDeviceEnumerator> deviceEnumerator;
    ComPtr<IMMDevice> defaultDevice;
    ComPtr<IAudioSessionManager2> sessionManager;
    std::vector<AudioSessionInfo> sessions;
    bool comInitialized = false;
    
public:
    AudioSessionEnumerator() {
        HRESULT hr = CoInitializeEx(nullptr, COINIT_MULTITHREADED);
        if (SUCCEEDED(hr)) {
            comInitialized = true;
        } else if (hr == RPC_E_CHANGED_MODE) {
            comInitialized = false;
        }
        
        Initialize();
    }
    
    ~AudioSessionEnumerator() {
        if (comInitialized) {
            CoUninitialize();
        }
    }
    
    bool Initialize() {
        HRESULT hr;
        
        // Create device enumerator
        hr = CoCreateInstance(__uuidof(MMDeviceEnumerator), nullptr,
            CLSCTX_ALL, __uuidof(IMMDeviceEnumerator),
            reinterpret_cast<void**>(deviceEnumerator.GetAddressOf()));
        
        if (FAILED(hr)) return false;
        
        // Get default audio endpoint
        hr = deviceEnumerator->GetDefaultAudioEndpoint(
            eRender, eConsole, &defaultDevice);
        
        if (FAILED(hr)) return false;
        
        // Get session manager
        hr = defaultDevice->Activate(__uuidof(IAudioSessionManager2),
            CLSCTX_ALL, nullptr,
            reinterpret_cast<void**>(sessionManager.GetAddressOf()));
        
        return SUCCEEDED(hr);
    }
    
    std::vector<AudioSessionInfo> EnumerateSessions() {
        sessions.clear();
        
        if (!sessionManager) return sessions;
        
        ComPtr<IAudioSessionEnumerator> sessionEnumerator;
        HRESULT hr = sessionManager->GetSessionEnumerator(&sessionEnumerator);
        
        if (FAILED(hr)) return sessions;
        
        int sessionCount = 0;
        hr = sessionEnumerator->GetCount(&sessionCount);
        
        if (FAILED(hr)) return sessions;
        
        for (int i = 0; i < sessionCount; i++) {
            ComPtr<IAudioSessionControl> sessionControl;
            hr = sessionEnumerator->GetSession(i, &sessionControl);
            
            if (FAILED(hr)) continue;
            
            // Get extended session control
            ComPtr<IAudioSessionControl2> sessionControl2;
            hr = sessionControl.As(&sessionControl2);
            
            if (FAILED(hr)) continue;
            
            AudioSessionInfo info = {};
            
            // Get process ID
            hr = sessionControl2->GetProcessId(&info.processId);
            if (FAILED(hr) || info.processId == 0) continue;
            
            // Get session state
            hr = sessionControl->GetState(&info.state);
            
            // Get session ID
            LPWSTR sessionId = nullptr;
            hr = sessionControl2->GetSessionIdentifier(&sessionId);
            if (SUCCEEDED(hr) && sessionId) {
                info.sessionId = sessionId;
                CoTaskMemFree(sessionId);
            }
            
            // Get display name
            LPWSTR displayName = nullptr;
            hr = sessionControl->GetDisplayName(&displayName);
            if (SUCCEEDED(hr) && displayName) {
                std::wstring wname(displayName);
                info.displayName = std::string(wname.begin(), wname.end());
                CoTaskMemFree(displayName);
            }
            
            // Get process name
            info.processName = GetProcessName(info.processId);
            
            // Get volume control
            ComPtr<ISimpleAudioVolume> volumeControl;
            hr = sessionControl2.As(&volumeControl);
            if (SUCCEEDED(hr)) {
                volumeControl->GetMasterVolume(&info.volume);
                BOOL muted = FALSE;
                volumeControl->GetMute(&muted);
                info.muted = (muted == TRUE);
            }
            
            sessions.push_back(info);
        }
        
        return sessions;
    }
    
    std::string GetProcessName(DWORD processId) {
        std::string processName = "Unknown";
        
        // First try with PROCESS_QUERY_LIMITED_INFORMATION (works for more processes)
        HANDLE hProcess = OpenProcess(
            PROCESS_QUERY_LIMITED_INFORMATION,
            FALSE, processId);
        
        if (hProcess) {
            char buffer[MAX_PATH];
            DWORD bufferSize = MAX_PATH;
            
            // Use QueryFullProcessImageNameA for better compatibility
            if (QueryFullProcessImageNameA(hProcess, 0, buffer, &bufferSize)) {
                // Extract filename from full path
                std::string fullPath(buffer);
                size_t lastSlash = fullPath.find_last_of("\\/");
                if (lastSlash != std::string::npos) {
                    processName = fullPath.substr(lastSlash + 1);
                } else {
                    processName = fullPath;
                }
            }
            CloseHandle(hProcess);
        }
        
        // If failed, try with higher privileges
        if (processName == "Unknown") {
            hProcess = OpenProcess(
                PROCESS_QUERY_INFORMATION | PROCESS_VM_READ,
                FALSE, processId);
            
            if (hProcess) {
                char buffer[MAX_PATH];
                if (GetModuleBaseNameA(hProcess, nullptr, buffer, MAX_PATH)) {
                    processName = buffer;
                }
                CloseHandle(hProcess);
            }
        }
        
        return processName;
    }
    
    bool SetSessionVolume(DWORD processId, float volume) {
        auto sessions = EnumerateSessions();
        
        for (const auto& session : sessions) {
            if (session.processId == processId) {
                // Re-get the session control to modify volume
                ComPtr<IAudioSessionEnumerator> sessionEnumerator;
                HRESULT hr = sessionManager->GetSessionEnumerator(&sessionEnumerator);
                if (FAILED(hr)) return false;
                
                int sessionCount = 0;
                hr = sessionEnumerator->GetCount(&sessionCount);
                if (FAILED(hr)) return false;
                
                for (int i = 0; i < sessionCount; i++) {
                    ComPtr<IAudioSessionControl> sessionControl;
                    hr = sessionEnumerator->GetSession(i, &sessionControl);
                    if (FAILED(hr)) continue;
                    
                    ComPtr<IAudioSessionControl2> sessionControl2;
                    hr = sessionControl.As(&sessionControl2);
                    if (FAILED(hr)) continue;
                    
                    DWORD pid = 0;
                    hr = sessionControl2->GetProcessId(&pid);
                    if (FAILED(hr) || pid != processId) continue;
                    
                    ComPtr<ISimpleAudioVolume> volumeControl;
                    hr = sessionControl2.As(&volumeControl);
                    if (SUCCEEDED(hr)) {
                        hr = volumeControl->SetMasterVolume(volume, nullptr);
                        return SUCCEEDED(hr);
                    }
                }
            }
        }
        
        return false;
    }
};

// Simple WASAPI loopback capture (system-wide)
class SimpleLoopbackCapture {
private:
    ComPtr<IAudioClient> audioClient;
    ComPtr<IAudioCaptureClient> captureClient;
    std::vector<float> buffer;
    std::mutex bufferMutex;
    bool isCapturing = false;
    bool comInitialized = false;
    
public:
    SimpleLoopbackCapture() {
        HRESULT hr = CoInitializeEx(nullptr, COINIT_MULTITHREADED);
        if (SUCCEEDED(hr)) {
            comInitialized = true;
        } else if (hr == RPC_E_CHANGED_MODE) {
            comInitialized = false;
        }
    }
    
    ~SimpleLoopbackCapture() {
        Stop();
        if (comInitialized) {
            CoUninitialize();
        }
    }
    
    bool Start() {
        if (isCapturing) return false;
        
        HRESULT hr;
        
        // Get default audio device
        ComPtr<IMMDeviceEnumerator> deviceEnumerator;
        hr = CoCreateInstance(__uuidof(MMDeviceEnumerator), nullptr,
            CLSCTX_ALL, __uuidof(IMMDeviceEnumerator),
            reinterpret_cast<void**>(deviceEnumerator.GetAddressOf()));
        
        if (FAILED(hr)) return false;
        
        ComPtr<IMMDevice> device;
        hr = deviceEnumerator->GetDefaultAudioEndpoint(
            eRender, eConsole, &device);
        
        if (FAILED(hr)) return false;
        
        // Activate audio client
        hr = device->Activate(__uuidof(IAudioClient),
            CLSCTX_ALL, nullptr,
            reinterpret_cast<void**>(audioClient.GetAddressOf()));
        
        if (FAILED(hr)) return false;
        
        // Get mix format
        WAVEFORMATEX* format = nullptr;
        hr = audioClient->GetMixFormat(&format);
        if (FAILED(hr)) return false;
        
        // Initialize in loopback mode
        hr = audioClient->Initialize(
            AUDCLNT_SHAREMODE_SHARED,
            AUDCLNT_STREAMFLAGS_LOOPBACK,
            0, 0, format, nullptr);
        
        CoTaskMemFree(format);
        
        if (FAILED(hr)) return false;
        
        // Get capture client
        hr = audioClient->GetService(__uuidof(IAudioCaptureClient),
            reinterpret_cast<void**>(captureClient.GetAddressOf()));
        
        if (FAILED(hr)) return false;
        
        // Start capture
        hr = audioClient->Start();
        if (FAILED(hr)) return false;
        
        isCapturing = true;
        return true;
    }
    
    void Stop() {
        if (isCapturing && audioClient) {
            audioClient->Stop();
            isCapturing = false;
        }
    }
    
    py::array_t<float> GetBuffer() {
        if (!isCapturing || !captureClient) {
            return py::array_t<float>(0);
        }
        
        std::lock_guard<std::mutex> lock(bufferMutex);
        buffer.clear();
        
        UINT32 packetLength = 0;
        HRESULT hr = captureClient->GetNextPacketSize(&packetLength);
        
        while (SUCCEEDED(hr) && packetLength > 0) {
            BYTE* data = nullptr;
            UINT32 numFramesAvailable;
            DWORD flags;
            
            hr = captureClient->GetBuffer(
                &data, &numFramesAvailable, &flags,
                nullptr, nullptr);
            
            if (SUCCEEDED(hr)) {
                if (!(flags & AUDCLNT_BUFFERFLAGS_SILENT)) {
                    // Assuming float format
                    float* floatData = reinterpret_cast<float*>(data);
                    buffer.insert(buffer.end(), 
                        floatData, 
                        floatData + numFramesAvailable * 2); // stereo
                }
                
                captureClient->ReleaseBuffer(numFramesAvailable);
            }
            
            hr = captureClient->GetNextPacketSize(&packetLength);
        }
        
        auto result = py::array_t<float>(buffer.size());
        auto ptr = static_cast<float*>(result.mutable_unchecked<1>().mutable_data(0));
        std::copy(buffer.begin(), buffer.end(), ptr);
        
        return result;
    }
};

PYBIND11_MODULE(_pywac_native, m) {
    m.doc() = "PyWAC - Python Windows Audio Capture";
    
    py::class_<AudioSessionInfo>(m, "AudioSessionInfo")
        .def_readonly("process_id", &AudioSessionInfo::processId)
        .def_readonly("process_name", &AudioSessionInfo::processName)
        .def_readonly("display_name", &AudioSessionInfo::displayName)
        .def_readonly("volume", &AudioSessionInfo::volume)
        .def_readonly("muted", &AudioSessionInfo::muted)
        .def_readonly("state", &AudioSessionInfo::state);
    
    py::class_<AudioSessionEnumerator>(m, "SessionEnumerator")
        .def(py::init<>())
        .def("enumerate_sessions", &AudioSessionEnumerator::EnumerateSessions,
             "Enumerate all audio sessions")
        .def("set_session_volume", &AudioSessionEnumerator::SetSessionVolume,
             "Set volume for a specific process",
             py::arg("process_id"), py::arg("volume"));
    
    py::class_<SimpleLoopbackCapture>(m, "SimpleLoopback")
        .def(py::init<>())
        .def("start", &SimpleLoopbackCapture::Start,
             "Start system-wide loopback capture")
        .def("stop", &SimpleLoopbackCapture::Stop,
             "Stop capture")
        .def("get_buffer", &SimpleLoopbackCapture::GetBuffer,
             "Get captured audio buffer");
    
    // Audio session state enum
    py::enum_<AudioSessionState>(m, "SessionState")
        .value("Inactive", AudioSessionStateInactive)
        .value("Active", AudioSessionStateActive)
        .value("Expired", AudioSessionStateExpired);
}