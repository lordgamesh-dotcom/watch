plugins { alias(libs.plugins.android.application) }
android {
    namespace = "com.example.cyberpunkface.watchface"
    enableKotlin = false
    compileSdk = 36
    defaultConfig {
        applicationId = providers.gradleProperty("applicationIdBase").get() + ".watchface"
        minSdk = 34
        targetSdk = 35
        versionCode = 1
        versionName = "1.0"
    }
}
