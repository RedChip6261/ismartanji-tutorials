package com.ismartanji.mobileai.ui

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.ismartanji.mobileai.data.OnDeviceAiRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

sealed interface UiState {
    object Idle : UiState
    object Loading : UiState
    data class Success(val outputText: String) : UiState
    data class Error(val message: String) : UiState
}

class LocalAssistantViewModel(
    private val repository: OnDeviceAiRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow<UiState>(UiState.Idle)
    val uiState: StateFlow<UiState> = _uiState.asStateFlow()

    init {
        viewModelScope.launch {
            repository.initializeModel()
                .onFailure { _uiState.value = UiState.Error("Device incompatible or model downloading.") }
        }
    }

    fun summarizeText(inputText: String) {
        viewModelScope.launch {
            _uiState.value = UiState.Loading
            var accumulatedText = ""
            
            try {
                val prompt = "Summarize the following notes concisely in three bullet points:\n$inputText"
                repository.generateStreamingResponse(prompt).collect { token ->
                    accumulatedText += token
                    _uiState.value = UiState.Success(accumulatedText)
                }
            } catch (e: Exception) {
                _uiState.value = UiState.Error("Generation failed: ${e.localizedMessage}")
            }
        }
    }
}
