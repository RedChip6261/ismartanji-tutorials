# Building On-Device AI Apps on Android: AICore Implementation & Practical Architecture

Companion code for the tutorial on ISMARTANJI CREATIONS:
https://ismartanji.com/how-to-build-on-device-ai-apps-android-2026/

## Files
- `app/build.gradle.kts.snippet`
- `app/src/main/java/com/ismartanji/mobileai/data/OnDeviceAiRepository.kt`
- `app/src/main/java/com/ismartanji/mobileai/ui/AiViewModel.kt`
- `app/src/main/java/com/ismartanji/mobileai/ui/AiScreen.kt`

## Setup
Copy the dependency lines from `app/build.gradle.kts.snippet` into your app module's `build.gradle.kts`, then drop the Kotlin files into `com.ismartanji.mobileai`. Requires an AICore-supported device (e.g. Pixel 9 series).

Read the full article for architecture, explanations and caveats.
