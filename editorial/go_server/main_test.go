package main

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"slices"
	"strings"
	"testing"
)

func TestRoutes(t *testing.T) {
	mux := routes()
	cases := []struct {
		name, method, path string
		status             int
		key, value         string
	}{
		{"health", "GET", "/healthz", http.StatusOK, "status", "ok"},
		{"greeting", "GET", "/api/hello/Ada", http.StatusOK, "message", "Hello, Ada!"},
		{"unicode", "GET", "/api/hello/Анна-Мария", http.StatusOK, "message", "Hello, Анна-Мария!"},
		{"validation", "GET", "/api/hello/Ada123", http.StatusBadRequest, "error", "Use 1 to 40 characters: letters and optional single hyphens between them."},
		{"missing", "GET", "/missing", http.StatusNotFound, "", ""},
		{"method", "POST", "/healthz", http.StatusMethodNotAllowed, "", ""},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			reply := httptest.NewRecorder()
			mux.ServeHTTP(reply, httptest.NewRequest(tc.method, tc.path, nil))
			if reply.Code != tc.status {
				t.Fatalf("status = %d, want %d", reply.Code, tc.status)
			}
			if tc.status == http.StatusMethodNotAllowed {
				allowed := strings.Split(reply.Header().Get("Allow"), ", ")
				if !slices.Contains(allowed, "GET") {
					t.Fatalf("Allow = %v, want GET", allowed)
				}
			}
			if tc.key == "" {
				return
			}
			if contentType := reply.Header().Get("Content-Type"); contentType != "application/json" {
				t.Fatalf("Content-Type = %q, want application/json", contentType)
			}
			var payload map[string]string
			if err := json.Unmarshal(reply.Body.Bytes(), &payload); err != nil {
				t.Fatal(err)
			}
			if payload[tc.key] != tc.value {
				t.Errorf("payload = %v, want %s = %q", payload, tc.key, tc.value)
			}
		})
	}
}
