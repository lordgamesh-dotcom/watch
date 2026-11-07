plugins { alias(libs.plugins.android.application) }
android {
    namespace = "com.example.cyberpunkface.wasteland"
    enableKotlin = false
    compileSdk = 36
    defaultConfig {
        applicationId = providers.gradleProperty("applicationIdBase").get() + ".wasteland"
        minSdk = 34
        targetSdk = 35
        versionCode = 1
        versionName = "1.0"
    }
}
