package com.example.androidtest;

import android.app.Activity;
import android.os.Bundle;
import android.os.Handler;
import android.webkit.WebView;
import android.webkit.WebViewClient;
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

    private TextView logView;
    private final Handler handler = new Handler();

    private void resetLog() {
        try {
            File logFile = new File(getFilesDir(), "startup.log");

            if (logFile.exists()) {
                logFile.delete();
            }

            logFile.createNewFile();

        } catch (Exception ignored) {
        }
    }

    private void writeLog(String text) {
        try {
            FileOutputStream fos =
                    openFileOutput("startup.log", MODE_APPEND);

            PrintWriter out = new PrintWriter(fos);
            out.println(text);
            out.flush();
            out.close();

        } catch (Exception ignored) {
        }
    }

    private String readLog() {
        try {
            FileInputStream fis = openFileInput("startup.log");

            BufferedReader reader = new BufferedReader(
                    new InputStreamReader(fis)
            );

            StringBuilder result = new StringBuilder();
            String line;

            while ((line = reader.readLine()) != null) {
                result.append(line).append("\n");
            }

            reader.close();
            fis.close();

            return result.toString();

        } catch (Exception e) {
            return "BRAK LOGU\n\n" + e;
        }
    }

    private void refreshLog() {
        if (logView != null) {
            logView.setText(readLog());
        }
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        resetLog();

        writeLog("========================================");
        writeLog("NOWE URUCHOMIENIE APK");
        writeLog("MainActivity.onCreate()");
        writeLog("APK START");
        writeLog("========================================");

        LinearLayout main = new LinearLayout(this);
        main.setOrientation(LinearLayout.VERTICAL);

        Button refreshButton = new Button(this);
        refreshButton.setText("ODŚWIEŻ LOG");

        logView = new TextView(this);
        logView.setTextSize(14);
        logView.setPadding(20, 20, 20, 20);
        logView.setTextIsSelectable(true);

        ScrollView scroll = new ScrollView(this);
        scroll.addView(logView);

        main.addView(
                refreshButton,
                new LinearLayout.LayoutParams(-1, -2)
        );

        main.addView(
                scroll,
                new LinearLayout.LayoutParams(-1, 0, 1)
        );

        setContentView(main);

        refreshButton.setOnClickListener(v -> refreshLog());

        refreshLog();

        /*
         * START PYTHONA W OSOBNYM WĄTKU.
         *
         * server.serve() działa cały czas, więc NIE MOŻEMY
         * czekać tutaj na jego zakończenie.
         */
        new Thread(() -> {

            try {
                writeLog("Uruchamiam Chaquopy...");

                if (!Python.isStarted()) {
                    Python.start(new AndroidPlatform(this));
                }

                writeLog("Python uruchomiony.");
                writeLog("Ładuję moduł server...");

                String logPath =
                        new File(
                                getFilesDir(),
                                "startup.log"
                        ).getAbsolutePath();

                writeLog("Python log path:");
                writeLog(logPath);

                writeLog("START server.start_server()...");

                /*
                 * Ta funkcja będzie działała cały czas.
                 */
                Python.getInstance()
                        .getModule("server")
                        .callAttr(
                                "start_server",
                                logPath
                        );

                /*
                 * Tutaj normalnie NIE dojdziemy,
                 * dopóki serwer działa.
                 */
                writeLog("server.start_server() zakończony.");

                handler.post(this::refreshLog);

            } catch (Exception e) {

                writeLog("!!! BŁĄD CHAQUOPY / PYTHON !!!");
                writeLog(e.toString());

                StringBuilder stack = new StringBuilder();

                for (StackTraceElement element : e.getStackTrace()) {
                    stack.append(element.toString()).append("\n");
                }

                writeLog(stack.toString());

                handler.post(this::refreshLog);
            }

        }).start();

        /*
         * WebView uruchamiamy NIEZALEŻNIE od Pythonowego wątku.
         *
         * Uvicorn potrzebuje chwili na start.
         */
        handler.postDelayed(() -> {

            writeLog("========================================");
            writeLog("URUCHAMIAM WEBVIEW");
            writeLog("http://127.0.0.1:8000/");
            writeLog("========================================");

            refreshLog();

            WebView webView = new WebView(this);

            webView.setWebViewClient(new WebViewClient());

            webView.getSettings().setJavaScriptEnabled(true);
            webView.getSettings().setDomStorageEnabled(true);

            webView.loadUrl(
                    "http://127.0.0.1:8000/"
            );

            setContentView(webView);

        }, 3000);

        /*
         * Odświeżanie logu podczas startu.
         */
        handler.postDelayed(this::refreshLog, 1000);
        handler.postDelayed(this::refreshLog, 3000);
        handler.postDelayed(this::refreshLog, 5000);
        handler.postDelayed(this::refreshLog, 8000);
    }
}
