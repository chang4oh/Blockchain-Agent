FROM golang:1.17-alpine as builder

WORKDIR /app

COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o risk-management-service .

FROM alpine:latest

WORKDIR /app
COPY --from=builder /app/risk-management-service .

EXPOSE 8080

CMD ["./risk-management-service"] 