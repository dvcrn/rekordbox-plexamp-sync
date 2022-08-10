.PHONY: build
build:
	go build -buildmode=c-shared -o library.so main.go
