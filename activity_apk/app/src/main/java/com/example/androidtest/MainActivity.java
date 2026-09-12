package com.example.activity;

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
import java.io.StringWriter;

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
        // EKRAN KONTROLNY
        // ============================================

        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);

        Button openButton = new Button(this);
        openButton.setText("OTWÓRZ ACTIVITY");

        openButton.setOnClickListener(v -> showWebView());

        layout.addView(openButton);

        Button deleteDbButton = new Button(this);
        deleteDbButton.setText("USUŃ BAZĘ SQLITE");

        deleteDbButton.setOnClickListener(v -> {

            File dbFile = new File(
                    getFilesDir(),
                    "activity.db"
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
                        appendLog("SUKCES!");
                        appendLog("BAZA ZOSTAŁA FIZYCZNIE USUNIĘTA");
                    } else {
                        appendLog("BŁĄD!");
                        appendLog("delete() zwróciło FALSE");
                    }

                } else {

                    appendLog("BAZA NIE ISTNIEJE.");
                    appendLog("Nie ma czego usuwać.");
                }

            } catch (Throwable e) {

                appendLog("WYJĄTEK PODCZAS USUWANIA BAZY");
                appendLog(e.toString());

                StringWriter sw = new StringWriter();
                e.printStackTrace(new PrintWriter(sw));
                appendLog(sw.toString());
            }

            if (!dbFile.exists()) {
                appendLog("KONTROLA: activity.db NIE ISTNIEJE.");
            } else {
                appendLog("KONTROLA: activity.db NADAL ISTNIEJE.");
            }
        });

        layout.addView(deleteDbButton);

        Button refreshButton = new Button(this);
        refreshButton.setText("ODŚWIEŻ LOG");

        refreshButton.setOnClickListener(v -> refreshLog());

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

        // ============================================
        // NAJPIERW POKAZUJEMY EKRAN LOGU
        // ============================================

        setContentView(layout);

        appendLog("========================================");
        appendLog("ACTIVITY APK - START");
        appendLog("========================================");
        appendLog("Ekran uruchomiony.");
        appendLog("Uruchamiam Python...");

        // ============================================
        // PYTHON
        // ============================================

        try {

            if (!Python.isStarted()) {
                Python.start(new AndroidPlatform(this));
            }

            appendLog("Python uruchomiony.");

        } catch (Throwable e) {

            appendLog("!!! BŁĄD URUCHAMIANIA PYTHON !!!");
            appendLog(e.toString());

            StringWriter sw = new StringWriter();
            e.printStackTrace(new PrintWriter(sw));
            appendLog(sw.toString());

            return;
        }

        // ============================================
        // START FASTAPI W TLE
        // ============================================

        Thread pythonThread = new Thread(() -> {

            try {

                appendLog("Pobieram instancję Python...");

                Python py = Python.getInstance();

                appendLog("Importuję moduł server...");

                py.getModule("server")
                        .callAttr(
                                "start_server",
                                logPath
                        );

            } catch (Throwable e) {

                appendLog("!!! BŁĄD STARTU FASTAPI !!!");
                appendLog(e.toString());

                StringWriter sw = new StringWriter();
                e.printStackTrace(new PrintWriter(sw));
                appendLog(sw.toString());
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
    }

    // =================================================
    // WEBVIEW
    // =================================================

    private void showWebView() {

        WebView webView = new WebView(this);

        webView.setWebViewClient(new WebViewClient());

        webView.setWebChromeClient(new WebChromeClient());

        webView.getSettings().setJavaScriptEnabled(true);
        webView.getSettings().setDomStorageEnabled(true);

        webView.loadUrl("http://127.0.0.1:8000/");

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

            StringBuilder text = new StringBuilder();

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

            logView.setText(text.toString());

            logView.post(() -> {

                if (logView.getLayout() != null) {

                    int scrollAmount =
                            logView.getLayout()
                                    .getLineTop(logView.getLineCount())
                            - logView.getHeight();

                    if (scrollAmount > 0) {
                        logView.scrollTo(0, scrollAmount);
                    }
                }
            });

        } catch (Throwable e) {

            logView.setText(
                    "Błąd odczytu logu:\n" + e
            );
        }
    }

    // =================================================
    // DODAJ WPIS DO LOGU
    // =================================================

    private void appendLog(String text) {

        try {

            File file = new File(logPath);

            FileOutputStream output =
                    new FileOutputStream(file, true);

            output.write(
                    (text + "\n").getBytes("UTF-8")
            );

            output.close();

            if (logView != null) {
                refreshLog();
            }

        } catch (Throwable ignored) {
        }
    }
}
