package org.jarvis.jarvis;

import android.accessibilityservice.AccessibilityService;
import android.accessibilityservice.AccessibilityServiceInfo;
import android.content.Intent;
import android.util.Log;
import android.view.accessibility.AccessibilityEvent;
import android.view.accessibility.AccessibilityNodeInfo;

import java.util.List;

/**
 * Servicio de Accesibilidad para Jarvis
 * Monitorea SMS y simula interacciones con la interfaz
 */
public class JarvisAccessibilityService extends AccessibilityService {
    
    private static final String TAG = "JarvisAccessibility";
    private static final String SMS_PACKAGE = "com.android.mms";
    private static final String SMS_PACKAGE_ALT = "com.google.android.apps.messaging";
    
    @Override
    public void onAccessibilityEvent(AccessibilityEvent event) {
        // Detectar eventos de SMS
        if (event.getPackageName() != null) {
            String packageName = event.getPackageName().toString();
            
            // Verificar si es app de SMS
            if (packageName.contains("sms") || 
                packageName.equals(SMS_PACKAGE) || 
                packageName.equals(SMS_PACKAGE_ALT) ||
                packageName.contains("messaging")) {
                
                Log.d(TAG, "SMS App detectada: " + packageName);
                
                // Capturar contenido de la pantalla
                AccessibilityNodeInfo rootNode = getRootInActiveWindow();
                if (rootNode != null) {
                    String screenContent = getScreenContent(rootNode);
                    Log.d(TAG, "Contenido de pantalla: " + screenContent);
                    
                    // Enviar al backend
                    sendToBackend(screenContent);
                }
            }
        }
    }
    
    @Override
    public void onInterrupt() {
        Log.d(TAG, "Servicio interrumpido");
    }
    
    @Override
    protected void onServiceConnected() {
        Log.d(TAG, "Servicio de accesibilidad conectado");
        
        // Configurar el servicio
        AccessibilityServiceInfo info = new AccessibilityServiceInfo();
        info.eventTypes = AccessibilityEvent.TYPES_ALL_MASK;
        info.feedbackType = AccessibilityServiceInfo.FEEDBACK_GENERIC;
        info.flags = AccessibilityServiceInfo.FLAG_INCLUDE_NOT_IMPORTANT_VIEWS;
        
        setServiceInfo(info);
    }
    
    /**
     * Extraer contenido de texto de la pantalla
     */
    private String getScreenContent(AccessibilityNodeInfo nodeInfo) {
        StringBuilder content = new StringBuilder();
        
        if (nodeInfo == null) {
            return content.toString();
        }
        
        // Obtener texto del nodo actual
        if (nodeInfo.getText() != null) {
            content.append(nodeInfo.getText()).append("\n");
        }
        
        // Recorrer nodos hijos
        for (int i = 0; i < nodeInfo.getChildCount(); i++) {
            AccessibilityNodeInfo child = nodeInfo.getChild(i);
            if (child != null) {
                content.append(getScreenContent(child));
            }
        }
        
        return content.toString();
    }
    
    /**
     * Simular toque en una posición
     */
    public void performClick(int x, int y) {
        Log.d(TAG, "Simulando toque en: " + x + ", " + y);
        // Usar GestureDescription para simular toque
    }
    
    /**
     * Simular escritura de texto
     */
    public void performType(String text) {
        Log.d(TAG, "Simulando escritura: " + text);
        // Usar InputMethodManager para escribir
    }
    
    /**
     * Enviar contenido al backend
     */
    private void sendToBackend(String content) {
        // Este método será llamado desde Python/Kivy
        Log.d(TAG, "Enviando al backend: " + content);
    }
}
