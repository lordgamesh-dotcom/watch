# Repository instructions

- The watch face modules (`watchface/`, `retrowave/`, `wasteland/`) are resource-only: keep `android:hasCode="false"` and do not add code to them.
- Keep built-in Kotlin disabled in `watchface/build.gradle.kts`, `retrowave/build.gradle.kts` and `wasteland/build.gradle.kts`; retain the phone companion as the only code-bearing module.
- Follow the official Watch Face Format documentation and the vendored WFF 2 schema. Never invent WFF elements or data sources.
- Keep identifiers and comments in English; localize user-visible strings with English fallback and pt-BR resources.
- Use JDK 17+, Android SDK, Gradle Kotlin DSL, and the version catalog.
- Build: `./gradlew :watchface:assembleDebug :retrowave:assembleDebug :wasteland:assembleDebug :phone:assembleDebug`.
- Release: `./gradlew :watchface:assembleRelease :retrowave:assembleRelease :wasteland:assembleRelease :phone:assembleRelease`.
- Validate: `scripts/validate-wff.sh`; install: `scripts/install.sh`.
- Run WFF XSD validation and memory footprint evaluation before release; document unavailable device/emulator checks.
