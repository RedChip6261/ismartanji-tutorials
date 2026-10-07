package com.ismartanji.mobileai.data

import android.content.Context
import com.google.ai.edge.aicore.GenerativeModel
import com.google.ai.edge.aicore.GenerationConfig
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

class OnDeviceAiRepository(private val context: Context) {

    private var generativeModel: GenerativeModel? = null

    suspend fun initializeModel(): Result<Unit> = withContext(Dispatchers.IO) {
        try {
            // Configure generation parameters optimized for mobile battery and latency
            val config = GenerationConfig.builder()
                .setTemperature(0.2f) // Lower temperature for factual, deterministic output
                .setTopK(16)
                .setMaxOutputTokens(256)
                .build()

            // Initialize connection to the shared system Gemini Nano service
            generativeModel = GenerativeModel(
                context = context,
                generationConfig = config
            )
            Result.success(Unit)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    fun generateStreamingResponse(prompt: String): Flow<String> = flow {
        val model = generativeModel 
            ?: throw IllegalStateException("Model has not been initialized yet.")

        // Stream tokens asynchronously as they are emitted from the local NPU
        val responseStream = model.generateContentStream(prompt)
        for (chunk in responseStream) {
            chunk.text?.let { emit(it) }
        }
    }
}
