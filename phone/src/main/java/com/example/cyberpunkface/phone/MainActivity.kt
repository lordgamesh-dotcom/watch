package com.example.cyberpunkface.phone

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.background
import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.res.painterResource
import com.google.android.gms.wearable.Wearable

private val Cyan = Color(0xFF19E6FF)

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent { MaterialTheme(colorScheme = darkColorScheme(primary = Cyan, background = Color.Black)) { CompanionScreen() } }
    }

    @Composable
    private fun CompanionScreen() {
        var status by remember { mutableStateOf(getString(R.string.checking)) }
        LaunchedEffect(Unit) {
            Wearable.getNodeClient(this@MainActivity).connectedNodes
                .addOnSuccessListener { nodes -> status = if (nodes.isEmpty()) getString(R.string.disconnected) else getString(R.string.connected) }
                .addOnFailureListener { status = getString(R.string.connection_error) }
        }
        Column(Modifier.fillMaxSize().background(Color(0xFF050B0E)).verticalScroll(rememberScrollState()).padding(24.dp), verticalArrangement = Arrangement.spacedBy(18.dp)) {
            Text(getString(R.string.title).uppercase(), color = Cyan, fontSize = 24.sp, fontWeight = FontWeight.Black)
            Box(Modifier.fillMaxWidth().height(230.dp).background(Color.Black), contentAlignment = Alignment.Center) {
                Image(painterResource(R.drawable.preview), contentDescription = getString(R.string.preview_description), modifier = Modifier.size(220.dp), contentScale = ContentScale.Fit)
            }
            Text(getString(R.string.connection), color = Cyan, fontWeight = FontWeight.Bold)
            Text(status, color = Color.White)
            Text(getString(R.string.instructions), color = Cyan, fontWeight = FontWeight.Bold)
            Text(getString(R.string.steps), color = Color.LightGray)
            Text(getString(R.string.adb_steps), color = Color.LightGray)
            Text(getString(R.string.privacy), color = Color(0xFF9FE8F2), fontSize = 13.sp)
        }
    }
}
