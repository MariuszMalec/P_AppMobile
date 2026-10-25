package com.example.androidtest;

import android.app.Activity;
import android.content.ContentValues;
import android.content.Intent;
import android.net.Uri;
import android.os.Build;
import android.os.Environment;
import android.provider.MediaStore;
import android.webkit.JavascriptInterface;
import android.webkit.ValueCallback;
import android.widget.Toast;
import java.io.InputStream;
import java.io.OutputStream;
import java.io.IOException;
import java.net.HttpURLConnection;
import java.net.URL;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;
import android.os.Bundle;
import android.os.Handler;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.webkit.WebChromeClient;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.InputStreamReader;
import java.io.PrintWriter;

public class MainActivity extends Activity {

    private Handler handler = new Handler();
    private TextView logView;
    private String logPath;
    private ValueCallback<Uri[]> filePathCallback;
    private static final int FILE_CHOOSER_REQUEST_CODE = 9124;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // ============================================
        // LOG
        // ============================================

        File logFile = new File(getFilesDir(), "startup.log");
        logPath = logFile.getAbsolutePath();

        try {
            PrintWriter writer = new PrintWriter(
                    new FileOutputStream(logFile, false)
            );
            writer.close();
        } catch (Exception ignored) {
        }

        // ============================================
        // PYTHON
        // ============================================

        if (!Python.isStarted()) {
            Python.start(new AndroidPlatform(this));
        }

        // ============================================
        // GŁÓWNY EKRAN KONTROLNY
        // ============================================

        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);

        // ============================================
        // OTWÓRZ MEETINGS
        // ============================================

        Button openButton = new Button(this);
        openButton.setText("OTWÓRZ MEETINGS");

        openButton.setOnClickListener(v -> {
            showWebView();
        });

        layout.addView(openButton);

        // ============================================
        // USUŃ BAZĘ
        // ============================================

        Button deleteDbButton = new Button(this);
        deleteDbButton.setText("USUŃ BAZĘ SQLITE");

        deleteDbButton.setOnClickListener(v -> {

            File dbFile = new File(
                    getFilesDir(),
                    "meetings.db"
            );

            appendLog("");
            appendLog("========================================");
            appendLog("PRÓBA USUNIĘCIA BAZY SQLITE");
            appendLog("========================================");
            appendLog("Ścieżka:");
            appendLog(dbFile.getAbsolutePath());

            try {

                if (dbFile.exists()) {

                    appendLog("Baza istnieje.");
                    appendLog("Rozmiar: " + dbFile.length() + " bajtów");

                    boolean deleted = dbFile.delete();

                    if (deleted) {

                        appendLog("========================================");
                        appendLog("SUKCES!");
                        appendLog("BAZA ZOSTAŁA FIZYCZNIE USUNIĘTA");
                        appendLog("========================================");

                    } else {

                        appendLog("========================================");
                        appendLog("BŁĄD!");
                        appendLog("delete() zwróciło FALSE");
                        appendLog("BAZA NIE ZOSTAŁA USUNIĘTA");
                        appendLog("========================================");
                    }

                } else {

                    appendLog("BAZA NIE ISTNIEJE.");
                    appendLog("Nie ma czego usuwać.");
                }

            } catch (Exception e) {

                appendLog("========================================");
                appendLog("WYJĄTEK PODCZAS USUWANIA BAZY");
                appendLog("========================================");
                appendLog(e.toString());
            }

            // Sprawdzenie po usunięciu
            if (!dbFile.exists()) {

                appendLog("");
                appendLog("KONTROLA:");
                appendLog("Plik meetings.db NIE ISTNIEJE.");

            } else {

                appendLog("");
                appendLog("KONTROLA:");
                appendLog("Plik meetings.db NADAL ISTNIEJE.");
            }
        });

        layout.addView(deleteDbButton);

        // ============================================
        // ODŚWIEŻ LOG
        // ============================================

        Button refreshButton = new Button(this);
        refreshButton.setText("ODŚWIEŻ LOG");

        refreshButton.setOnClickListener(v -> {
            refreshLog();
        });

        layout.addView(refreshButton);

        // ============================================
        // LOG
        // ============================================

        logView = new TextView(this);
        logView.setTextSize(14);
        logView.setTextIsSelectable(true);
        logView.setPadding(20, 20, 20, 20);

        ScrollView scrollView = new ScrollView(this);
        scrollView.addView(logView);

        layout.addView(
                scrollView,
                new LinearLayout.LayoutParams(
                        LinearLayout.LayoutParams.MATCH_PARENT,
                        0,
                        1
                )
        );

        if (BuildConfig.DEBUG) {
            setContentView(layout);
        }

        // ============================================
        // START FASTAPI W TLE
        // ============================================

        Thread pythonThread = new Thread(() -> {

            try {

                Python py = Python.getInstance();

                py.getModule("server")
                        .callAttr(
                                "start_server",
                                logPath
                        );

            } catch (Exception e) {

                appendLog("!!! BŁĄD PYTHON !!!");
                appendLog(e.toString());
            }
        });

        pythonThread.start();

        // ============================================
        // AUTOMATYCZNE ODŚWIEŻANIE LOGU
        // ============================================

        handler.postDelayed(new Runnable() {

            @Override
            public void run() {

                refreshLog();

                handler.postDelayed(this, 1000);
            }

        }, 1000);

        // ============================================
        // DEBUG / RELEASE
        // ============================================

        if (!BuildConfig.DEBUG) {

            // RELEASE:
            // automatycznie otwieramy Meetings
            // po krótkim czasie na uruchomienie FastAPI

            handler.postDelayed(() -> {
                showWebView();
            }, 1500);
        }
    }

    // =================================================
    // WEBVIEW
    // =================================================

    private void showWebView() {
        WebView webView = new WebView(this);

        webView.setWebViewClient(
            new WebViewClient() {
                @Override
                public boolean shouldOverrideUrlLoading(
                        WebView view,
                        android.webkit.WebResourceRequest request
                ) {
                    String url = request.getUrl().toString();

                    if (url.startsWith("tel:")
                            || url.startsWith("sms:")
                            || url.startsWith("smsto:")
                            || url.startsWith("mailto:")) {
                        try {
                            android.content.Intent intent =
                                new android.content.Intent(
                                    android.content.Intent.ACTION_VIEW,
                                    android.net.Uri.parse(url)
                                );
                            startActivity(intent);
                        } catch (Exception ignored) {
                        }
                        return true;
                    }

                    return false;
                }
            }
        );

        webView.setWebChromeClient(
            new WebChromeClient() {
                @Override
                public boolean onShowFileChooser(
                        WebView view,
                        ValueCallback<Uri[]> callback,
                        WebChromeClient.FileChooserParams params
                ) {
                    if (filePathCallback != null) {
                        filePathCallback.onReceiveValue(null);
                    }
                    filePathCallback = callback;

                    try {
                        Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
                        intent.addCategory(Intent.CATEGORY_OPENABLE);
                        intent.setType("*/*");
                        startActivityForResult(intent, FILE_CHOOSER_REQUEST_CODE);
                        return true;
                    } catch (Exception e) {
                        filePathCallback = null;
                        callback.onReceiveValue(null);
                        Toast.makeText(
                            MainActivity.this,
                            "Nie można otworzyć wyboru pliku.",
                            Toast.LENGTH_LONG
                        ).show();
                        return false;
                    }
                }
            }
        );

        webView.getSettings()
            .setJavaScriptEnabled(true);

        webView.getSettings()
            .setDomStorageEnabled(true);

        webView.getSettings()
            .setCacheMode(android.webkit.WebSettings.LOAD_NO_CACHE);

        webView.addJavascriptInterface(new Object() {
            @JavascriptInterface
            public void exportDatabase() {
                exportDatabaseToDownloads();
            }
        }, "AndroidBridge");

        webView.loadUrl(
            "http://127.0.0.1:8000/"
        );

        setContentView(webView);
    }

    @Override
    protected void onActivityResult(
            int requestCode,
            int resultCode,
            Intent data
    ) {
        if (requestCode == FILE_CHOOSER_REQUEST_CODE) {
            if (filePathCallback != null) {
                Uri[] results = WebChromeClient.FileChooserParams.parseResult(
                    resultCode, data
                );
                filePathCallback.onReceiveValue(results);
                filePathCallback = null;
            }
            return;
        }
        super.onActivityResult(requestCode, resultCode, data);
    }

    private void exportDatabaseToDownloads() {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.Q) {
            runOnUiThread(() ->
                Toast.makeText(
                    MainActivity.this,
                    "Eksport do Pobranych wymaga Androida 10 lub nowszego.",
                    Toast.LENGTH_LONG
                ).show()
            );
            return;
        }

        new Thread(() -> {
            Uri outputUri = null;
            HttpURLConnection connection = null;
            String fileName = "";

            try {
                URL url = new URL(
                    "http://127.0.0.1:8000/api/backup/export"
                );

                connection = (HttpURLConnection) url.openConnection();
                connection.setRequestMethod("GET");
                connection.setConnectTimeout(15000);
                connection.setReadTimeout(60000);

                int status = connection.getResponseCode();
                if (status != HttpURLConnection.HTTP_OK) {
                    throw new IOException(
                        "Serwer zwrócił HTTP " + status
                    );
                }

                String timestamp = new SimpleDateFormat(
                    "yyyyMMdd-HHmmss",
                    Locale.US
                ).format(new Date());

                fileName = "meetings-backup-" + timestamp + ".db";

                ContentValues values = new ContentValues();
                values.put(
                    MediaStore.MediaColumns.DISPLAY_NAME,
                    fileName
                );
                values.put(
                    MediaStore.MediaColumns.MIME_TYPE,
                    "application/octet-stream"
                );
                values.put(
                    MediaStore.MediaColumns.RELATIVE_PATH,
                    Environment.DIRECTORY_DOWNLOADS
                );
                values.put(
                    MediaStore.MediaColumns.IS_PENDING,
                    1
                );

                outputUri = getContentResolver().insert(
                    MediaStore.Downloads.EXTERNAL_CONTENT_URI,
                    values
                );

                if (outputUri == null) {
                    throw new IOException(
                        "Android nie utworzył pliku w Pobranych."
                    );
                }

                try (
                    InputStream input = connection.getInputStream();
                    OutputStream output =
                        getContentResolver().openOutputStream(outputUri)
                ) {
                    if (output == null) {
                        throw new IOException(
                            "Nie można zapisać pliku."
                        );
                    }

                    byte[] buffer = new byte[8192];
                    int count;

                    while ((count = input.read(buffer)) != -1) {
                        output.write(buffer, 0, count);
                    }

                    output.flush();
                }

                ContentValues completed = new ContentValues();
                completed.put(
                    MediaStore.MediaColumns.IS_PENDING,
                    0
                );

                int updated = getContentResolver().update(
                    outputUri,
                    completed,
                    null,
                    null
                );

                if (updated <= 0) {
                    throw new IOException(
                        "Nie udało się zakończyć zapisu pliku."
                    );
                }

                String savedName = fileName;
                runOnUiThread(() ->
                    Toast.makeText(
                        MainActivity.this,
                        "Kopia zapisana w Pobranych: " + savedName,
                        Toast.LENGTH_LONG
                    ).show()
                );

            } catch (Exception exc) {
                if (outputUri != null) {
                    try {
                        getContentResolver().delete(
                            outputUri,
                            null,
                            null
                        );
                    } catch (Exception ignored) {
                    }
                }

                String error = exc.getMessage();
                if (error == null || error.trim().isEmpty()) {
                    error = exc.getClass().getSimpleName();
                }

                final String message = "Eksport nieudany: " + error;

                runOnUiThread(() ->
                    Toast.makeText(
                        MainActivity.this,
                        message,
                        Toast.LENGTH_LONG
                    ).show()
                );

            } finally {
                if (connection != null) {
                    connection.disconnect();
                }
            }
        }).start();
    }

    // =================================================
    // LOG
    // =================================================

    private void refreshLog() {

        if (logView == null) {
            return;
        }

        try {

            File file = new File(logPath);

            if (!file.exists()) {
                return;
            }

            StringBuilder text =
                    new StringBuilder();

            BufferedReader reader =
                    new BufferedReader(
                            new InputStreamReader(
                                    new FileInputStream(file),
                                    "UTF-8"
                            )
                    );

            String line;

            while ((line = reader.readLine()) != null) {

                text.append(line);
                text.append("\n");
            }

            reader.close();

            logView.setText(
                    text.toString()
            );

            logView.post(() -> {

                if (logView.getLayout() != null) {

                    int scrollAmount =
                            logView.getLayout()
                                    .getLineTop(
                                            logView.getLineCount()
                                    )
                            - logView.getHeight();

                    if (scrollAmount > 0) {
                        logView.scrollTo(
                                0,
                                scrollAmount
                        );
                    }
                }
            });

        } catch (Exception e) {

            logView.setText(
                    "Błąd odczytu logu:\n"
                    + e
            );
        }
    }

    // =================================================
    // DODAJ WPIS DO LOGU
    // =================================================

    private void appendLog(String text) {

        try {

            File file =
                    new File(logPath);

            FileOutputStream output =
                    new FileOutputStream(
                            file,
                            true
                    );

            output.write(
                    (text + "\n")
                            .getBytes("UTF-8")
            );

            output.close();

            refreshLog();

        } catch (Exception ignored) {
        }
    }
}




