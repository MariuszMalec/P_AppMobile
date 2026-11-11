package com.example.androidtest;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.UUID;

public class GoogleDriveBackup {

    private static final String FILE_NAME = "Meetings-backup-Android.db";
    private static final String FILE_MARKER = "meetings-android-backup-v1";
    private static final String MIME_TYPE = "application/vnd.sqlite3";

    public interface ProgressCallback {
        void onStatus(String message);
    }

    public static JSONObject uploadAndShare(
            String accessToken,
            String recipientEmail,
            ProgressCallback callback
    ) throws Exception {

        if (accessToken == null || accessToken.trim().isEmpty()) {
            throw new Exception("Brak tokenu Google.");
        }

        if (recipientEmail == null ||
                !recipientEmail.matches("^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$")) {
            throw new Exception("Podaj prawidłowy adres e-mail odbiorcy.");
        }

        status(callback, "Pobieram aktualną bazę...");

        byte[] database = downloadDatabase();

        if (database.length == 0) {
            throw new Exception("Pobrana baza jest pusta.");
        }

        status(callback, "Szukam poprzedniej kopii Androida...");

        String query =
                "trashed = false and appProperties has " +
                "{ key='meetingsBackup' and value='" + FILE_MARKER + "' }";

        String searchUrl =
                "https://www.googleapis.com/drive/v3/files?q=" +
                URLEncoder.encode(query, "UTF-8") +
                "&fields=files(id,name,webViewLink)";

        JSONObject search = request(
                searchUrl,
                accessToken,
                "GET",
                null,
                null
        );

        JSONArray files = search.optJSONArray("files");
        JSONObject existing = files != null && files.length() > 0
                ? files.getJSONObject(0)
                : null;

        JSONObject file;

        if (existing != null) {
            status(callback, "Aktualizuję poprzednią kopię...");

            String fileId = existing.getString("id");

            file = request(
                    "https://www.googleapis.com/upload/drive/v3/files/" +
                            fileId +
                            "?uploadType=media&fields=id,name,webViewLink",
                    accessToken,
                    "PATCH",
                    MIME_TYPE,
                    database
            );

            file.put("updated", true);

        } else {
            status(callback, "Tworzę kopię na Dysku...");

            String boundary = "MeetingsBoundary" + UUID.randomUUID();

            JSONObject metadata = new JSONObject();
            metadata.put("name", FILE_NAME);
            metadata.put("mimeType", MIME_TYPE);

            JSONObject properties = new JSONObject();
            properties.put("meetingsBackup", FILE_MARKER);
            metadata.put("appProperties", properties);

            ByteArrayOutputStream body = new ByteArrayOutputStream();

            write(body, "--" + boundary + "\r\n");
            write(body, "Content-Type: application/json; charset=UTF-8\r\n\r\n");
            write(body, metadata.toString());
            write(body, "\r\n--" + boundary + "\r\n");
            write(body, "Content-Type: " + MIME_TYPE + "\r\n");
            write(body, "Content-Disposition: form-data; name=\"file\"; filename=\"" +
                    FILE_NAME + "\"\r\n\r\n");

            body.write(database);

            write(body, "\r\n--" + boundary + "--\r\n");

            file = request(
                    "https://www.googleapis.com/upload/drive/v3/files" +
                            "?uploadType=multipart&fields=id,name,webViewLink",
                    accessToken,
                    "POST",
                    "multipart/related; boundary=" + boundary,
                    body.toByteArray()
            );

            file.put("updated", false);
        }

        String fileId = file.getString("id");

        status(callback, "Sprawdzam dostęp odbiorcy...");

        JSONObject permissions = request(
                "https://www.googleapis.com/drive/v3/files/" +
                        fileId +
                        "/permissions?fields=permissions(id,type,role,emailAddress)",
                accessToken,
                "GET",
                null,
                null
        );

        JSONArray permissionList = permissions.optJSONArray("permissions");
        boolean recipientExists = false;

        if (permissionList != null) {
            for (int i = 0; i < permissionList.length(); i++) {
                JSONObject permission = permissionList.getJSONObject(i);

                String email = permission.optString("emailAddress", "");

                if ("user".equals(permission.optString("type")) &&
                        recipientEmail.equalsIgnoreCase(email)) {
                    recipientExists = true;
                    break;
                }
            }
        }

        if (!recipientExists) {
            status(callback, "Udostępniam kopię odbiorcy...");

            JSONObject permission = new JSONObject();
            permission.put("type", "user");
            permission.put("role", "reader");
            permission.put("emailAddress", recipientEmail);

            request(
                    "https://www.googleapis.com/drive/v3/files/" +
                            fileId +
                            "/permissions?sendNotificationEmail=true",
                    accessToken,
                    "POST",
                    "application/json; charset=UTF-8",
                    permission.toString().getBytes(StandardCharsets.UTF_8)
            );
        }

        file.put("name", file.optString("name", FILE_NAME));
        file.put("link", file.optString("webViewLink", ""));

        status(callback, "Kopia została zapisana na Dysku.");

        return file;
    }

    private static byte[] downloadDatabase() throws Exception {
        HttpURLConnection connection = null;

        try {
            connection = (HttpURLConnection)
                    new URL("http://127.0.0.1:8000/api/backup/export")
                            .openConnection();

            connection.setRequestMethod("GET");
            connection.setConnectTimeout(15000);
            connection.setReadTimeout(60000);

            int code = connection.getResponseCode();

            if (code != 200) {
                throw new Exception(
                        "Nie udało się pobrać bazy. HTTP " + code
                );
            }

            return readAll(connection.getInputStream());

        } finally {
            if (connection != null) {
                connection.disconnect();
            }
        }
    }

    private static JSONObject request(
            String address,
            String token,
            String method,
            String contentType,
            byte[] body
    ) throws Exception {

        HttpURLConnection connection = null;

        try {
            connection = (HttpURLConnection)
                    new URL(address).openConnection();

            connection.setRequestMethod(method);
            connection.setConnectTimeout(20000);
            connection.setReadTimeout(60000);
            connection.setRequestProperty(
                    "Authorization",
                    "Bearer " + token
            );

            if (body != null) {
                connection.setDoOutput(true);
                connection.setRequestProperty(
                        "Content-Type",
                        contentType
                );

                try (OutputStream output = connection.getOutputStream()) {
                    output.write(body);
                }
            }

            int code = connection.getResponseCode();

            InputStream stream = code >= 200 && code < 300
                    ? connection.getInputStream()
                    : connection.getErrorStream();

            byte[] responseBytes = stream != null
                    ? readAll(stream)
                    : new byte[0];

            String responseText = new String(
                    responseBytes,
                    StandardCharsets.UTF_8
            );

            if (code < 200 || code >= 300) {
                String message = "Google Drive: HTTP " + code;

                try {
                    JSONObject error = new JSONObject(responseText);
                    message += " — " +
                            error.optJSONObject("error")
                                    .optString("message", "");
                } catch (Exception ignored) {
                    if (!responseText.isEmpty()) {
                        message += " — " + responseText;
                    }
                }

                throw new Exception(message);
            }

            return responseText.isEmpty()
                    ? new JSONObject()
                    : new JSONObject(responseText);

        } finally {
            if (connection != null) {
                connection.disconnect();
            }
        }
    }

    private static byte[] readAll(InputStream input) throws Exception {
        try (InputStream stream = input;
             ByteArrayOutputStream output = new ByteArrayOutputStream()) {

            byte[] buffer = new byte[8192];
            int count;

            while ((count = stream.read(buffer)) != -1) {
                output.write(buffer, 0, count);
            }

            return output.toByteArray();
        }
    }

    private static void write(
            ByteArrayOutputStream output,
            String value
    ) throws Exception {
        output.write(value.getBytes(StandardCharsets.UTF_8));
    }

    private static void status(
            ProgressCallback callback,
            String message
    ) {
        if (callback != null) {
            callback.onStatus(message);
        }
    }
}
