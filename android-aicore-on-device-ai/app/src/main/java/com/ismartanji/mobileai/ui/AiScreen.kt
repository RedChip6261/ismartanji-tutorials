package com.ismartanji.mobileai.ui

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun OnDeviceAiScreen(
    viewModel: LocalAssistantViewModel,
    modifier: Modifier = Modifier
) {
    val uiState by viewModel.uiState.collectAsState()
    var userNotes by remember { mutableStateOf("") }

    Scaffold(
        topBar = { TopAppBar(title = { Text("Local Notes AI Assistant") }) },
        modifier = modifier
    ) { innerPadding ->
        Column(
            modifier = Modifier
                .padding(innerPadding)
                .padding(16.dp)
                .fillMaxSize()
                .verticalScroll(rememberScrollState()),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            OutlinedTextField(
                value = userNotes,
                onValueChange = { userNotes = it },
                label = { Text("Paste meeting notes or thoughts") },
                placeholder = { Text("Enter text for instant offline on-device summarization...") },
                modifier = Modifier.fillMaxWidth().height(150.dp)
            )

            Button(
                onClick = { viewModel.summarizeText(userNotes) },
                enabled = userNotes.isNotBlank() && uiState !is UiState.Loading,
                modifier = Modifier.fillMaxWidth()
            ) {
                Text("Summarize with On-Device AI")
            }

            when (val state = uiState) {
                is UiState.Idle -> {
                    Text(
                        text = "Ready for private, zero-latency inference.",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
                is UiState.Loading -> {
                    LinearProgressIndicator(modifier = Modifier.fillMaxWidth())
                    Text("Streaming tokens from local NPU...")
                }
                is UiState.Success -> {
                    Card(
                        colors = CardDefaults.cardColors(
                            containerColor = MaterialTheme.colorScheme.surfaceVariant
                        ),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Column(modifier = Modifier.padding(16.dp)) {
                            Text(
                                text = "Local Summary:",
                                style = MaterialTheme.typography.titleMedium
                            )
                            Spacer(modifier = Modifier.height(8.dp))
                            Text(
                                text = state.outputText,
                                style = MaterialTheme.typography.bodyLarge
                            )
                        }
                    }
                }
                is UiState.Error -> {
                    Text(
                        text = state.message,
                        color = MaterialTheme.colorScheme.error,
                        style = MaterialTheme.typography.bodyMedium
                    )
                }
            }
        }
    }
}
