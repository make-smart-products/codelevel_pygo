package main

import (
	"context"
	"encoding/json"
	"errors"
	"log"
	"net/http"
	"os"
	"os/signal"
	"strings"
	"syscall"
	"time"
	"unicode"
	"unicode/utf8"
)

func main() {
	if err := run(); err != nil {
		log.Fatal(err)
	}
}

func run() error {
	stop, cancelSignals := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer cancelSignals()

	server := &http.Server{
		Addr:              "127.0.0.1:8080",
		Handler:           routes(),
		ReadHeaderTimeout: 3 * time.Second,
		ReadTimeout:       10 * time.Second,
		WriteTimeout:      10 * time.Second,
		IdleTimeout:       60 * time.Second,
	}

	served := make(chan error, 1)
	go func() {
		log.Printf("Listening on http://%s", server.Addr)
		served <- server.ListenAndServe()
	}()

	select {
	case err := <-served:
		return err
	case <-stop.Done():
		cancelSignals()
		deadline, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()
		if err := server.Shutdown(deadline); err != nil {
			return err
		}
		if err := <-served; !errors.Is(err, http.ErrServerClosed) {
			return err
		}
		return nil
	}
}

func routes() http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("GET /healthz", health)
	mux.HandleFunc("GET /api/hello/{name}", hello)
	return mux
}

func health(w http.ResponseWriter, _ *http.Request) {
	writeJSON(w, http.StatusOK, map[string]string{"status": "ok"})
}

func hello(w http.ResponseWriter, r *http.Request) {
	name := r.PathValue("name")
	if !validName(name) {
		writeJSON(w, http.StatusBadRequest, map[string]string{
			"error": "Use 1 to 40 characters: letters and optional single hyphens between them.",
		})
		return
	}
	writeJSON(w, http.StatusOK, map[string]string{"message": "Hello, " + name + "!"})
}

func validName(name string) bool {
	length := utf8.RuneCountInString(name)
	if length < 1 || length > 40 {
		return false
	}
	for _, part := range strings.Split(name, "-") {
		if part == "" || strings.ContainsFunc(part, func(ch rune) bool { return !unicode.IsLetter(ch) }) {
			return false
		}
	}
	return true
}

func writeJSON(w http.ResponseWriter, status int, value map[string]string) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	if err := json.NewEncoder(w).Encode(value); err != nil {
		log.Printf("Write JSON: %v", err)
	}
}
