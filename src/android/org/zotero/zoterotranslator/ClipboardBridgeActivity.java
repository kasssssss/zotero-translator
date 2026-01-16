package org.zotero.zoterotranslator;

import android.app.Activity;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;

/**
 * Transparent Activity to read clipboard content.
 * 
 * On Android 10+ (API 29+), only the foreground app with input focus
 * can access clipboard. This activity briefly gains focus to read
 * clipboard, then immediately finishes.
 * 
 * Flow:
 * 1. Floating bubble click triggers startActivity() with request_id
 * 2. This activity starts (transparent, user barely notices)
 * 3. onWindowFocusChanged(true) fires when we have input focus
 * 4. After short delay, read clipboard and write to SharedPreferences
 * 5. finish() immediately, user returns to previous app
 * 6. Python code polls SharedPreferences and gets the clipboard text
 */
public class ClipboardBridgeActivity extends Activity {

    private static final String TAG = "ClipboardBridge";
    private static final String PREF_NAME = "zoterotranslator";
    private static final String EXTRA_REQUEST_ID = "request_id";
    
    // Keys for SharedPreferences
    private static final String KEY_CLIP_TEXT = "clip_text";
    private static final String KEY_CLIP_REQUEST_ID = "clip_request_id";
    private static final String KEY_CLIP_TIMESTAMP = "clip_ts";

    private boolean hasReadClipboard = false;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        Log.d(TAG, "onCreate - Activity created");
        // Don't read clipboard here! We don't have input focus yet.
        // Reading here will likely return null on Android 10+.
    }

    @Override
    public void onWindowFocusChanged(boolean hasFocus) {
        super.onWindowFocusChanged(hasFocus);
        Log.d(TAG, "onWindowFocusChanged: " + hasFocus);
        
        if (!hasFocus || hasReadClipboard) {
            return;
        }
        
        hasReadClipboard = true;

        // Delay slightly to ensure focus is fully established
        // This avoids race conditions where focus isn't quite ready
        new Handler(Looper.getMainLooper()).postDelayed(new Runnable() {
            @Override
            public void run() {
                readClipboardAndFinish();
            }
        }, 150);
    }

    private void readClipboardAndFinish() {
        String requestId = getIntent().getStringExtra(EXTRA_REQUEST_ID);
        Log.d(TAG, "Reading clipboard for request: " + requestId);

        String clipText = readClipboardText();
        Log.d(TAG, "Clipboard text length: " + (clipText != null ? clipText.length() : 0));

        // Write result to SharedPreferences
        SharedPreferences sp = getSharedPreferences(PREF_NAME, MODE_PRIVATE);
        sp.edit()
          .putString(KEY_CLIP_TEXT, clipText != null ? clipText : "")
          .putString(KEY_CLIP_REQUEST_ID, requestId != null ? requestId : "")
          .putLong(KEY_CLIP_TIMESTAMP, System.currentTimeMillis())
          .apply();

        Log.d(TAG, "Clipboard data saved to SharedPreferences");

        // Finish immediately - user returns to previous app
        finish();
        
        // No transition animation for seamless experience
        overridePendingTransition(0, 0);
    }

    private String readClipboardText() {
        try {
            ClipboardManager cm = (ClipboardManager) getSystemService(Context.CLIPBOARD_SERVICE);
            if (cm == null) {
                Log.w(TAG, "ClipboardManager is null");
                return "";
            }

            if (!cm.hasPrimaryClip()) {
                Log.d(TAG, "No primary clip available");
                return "";
            }

            ClipData clip = cm.getPrimaryClip();
            if (clip == null || clip.getItemCount() == 0) {
                Log.d(TAG, "Clip is null or empty");
                return "";
            }

            CharSequence text = clip.getItemAt(0).coerceToText(this);
            return text != null ? text.toString() : "";

        } catch (Exception e) {
            Log.e(TAG, "Error reading clipboard: " + e.getMessage());
            return "";
        }
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        Log.d(TAG, "onDestroy - Activity destroyed");
    }
}

