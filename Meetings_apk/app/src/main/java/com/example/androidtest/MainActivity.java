package com.example.androidtest;

import android.app.Activity;
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

        setContentView(layout);

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
        // WAŻNE:
        //
        // NIE URUCHAMIAMY AUTOMATYCZNIE WebView.
        //
        // Użytkownik sam naciska:
        // "OTWÓRZ MEETINGS"
        // ============================================
    }

    // =================================================
    // WEBVIEW
    // =================================================

    private void showWebView() {
        WebView webView = new WebView(this);

        webView.setWebViewClient(
            new WebViewClient()
        );

        webView.setWebChromeClient(
            new WebChromeClient()
        );

        webView.getSettings()
            .setJavaScriptEnabled(true);

        webView.getSettings()
            .setDomStorageEnabled(true);

        webView.loadUrl(
            "http://127.0.0.1:8000/"
        );

        setContentView(webView);
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
