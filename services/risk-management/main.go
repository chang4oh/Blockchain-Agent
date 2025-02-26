package main

import (
	"context"
	"encoding/json"
	"log"
	"net/http"
	"os"
	"strconv"
	"time"

	"github.com/go-redis/redis/v8"
	"github.com/gorilla/mux"
	"github.com/segmentio/kafka-go"
)

type TradeRequest struct {
	UserID  string  `json:"user_id"`
	Symbol  string  `json:"symbol"`
	Action  string  `json:"action"` // buy or sell
	Amount  float64 `json:"amount"`
	Price   float64 `json:"price"`
}

type RiskResponse struct {
	Approved bool   `json:"approved"`
	Reason   string `json:"reason,omitempty"`
}

type UserLimits struct {
	UserID      string  `json:"user_id"`
	DailyLimit  float64 `json:"daily_limit"`
	DailyTraded float64 `json:"daily_traded"`
	Remaining   float64 `json:"remaining"`
}

var ctx = context.Background()
var rdb *redis.Client
var kafkaWriter *kafka.Writer

func main() {
	// Initialize Redis
	redisAddr := os.Getenv("REDIS_ADDR")
	if redisAddr == "" {
		redisAddr = "localhost:6379"
	}
	
	rdb = redis.NewClient(&redis.Options{
		Addr: redisAddr,
	})

	// Initialize Kafka
	kafkaBroker := os.Getenv("KAFKA_BROKER")
	if kafkaBroker == "" {
		kafkaBroker = "localhost:9092"
	}
	
	kafkaWriter = &kafka.Writer{
		Addr:     kafka.TCP(kafkaBroker),
		Topic:    "risk-events",
		Balancer: &kafka.LeastBytes{},
	}

	// Set up API routes
	r := mux.NewRouter()
	r.HandleFunc("/", healthCheckHandler).Methods("GET")
	r.HandleFunc("/api/v1/risk/evaluate-trade", evaluateTradeHandler).Methods("POST")
	r.HandleFunc("/api/v1/risk/user-limits/{user_id}", getUserLimitsHandler).Methods("GET")
	
	// Start server
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}
	
	log.Printf("Risk Management Service starting on port %s", port)
	log.Fatal(http.ListenAndServe(":"+port, r))
}

func healthCheckHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{
		"status": "ok",
		"service": "risk-management",
	})
}

func evaluateTradeHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	
	var tradeReq TradeRequest
	if err := json.NewDecoder(r.Body).Decode(&tradeReq); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	// Check daily trading limit
	dailyLimit, err := getUserDailyLimit(tradeReq.UserID)
	if err != nil {
		log.Printf("Failed to get user limits: %v", err)
		http.Error(w, "Failed to get user limits", http.StatusInternalServerError)
		return
	}

	dailyTraded, err := getDailyTradedAmount(tradeReq.UserID)
	if err != nil {
		log.Printf("Failed to get daily traded amount: %v", err)
		http.Error(w, "Failed to get daily traded amount", http.StatusInternalServerError)
		return
	}

	if dailyTraded+tradeReq.Amount > dailyLimit {
		response := RiskResponse{
			Approved: false,
			Reason:   "Daily trading limit exceeded",
		}
		json.NewEncoder(w).Encode(response)
		
		// Log risk event to Kafka
		logRiskEvent(tradeReq, "REJECTED", "Daily trading limit exceeded")
		return
	}

	// Check for suspicious activity (large trades)
	if tradeReq.Amount > dailyLimit*0.5 {
		response := RiskResponse{
			Approved: false,
			Reason:   "Trade amount exceeds 50% of daily limit, requires manual approval",
		}
		json.NewEncoder(w).Encode(response)
		
		// Log risk event to Kafka
		logRiskEvent(tradeReq, "REJECTED", "Large trade requires manual approval")
		return
	}

	// Trade approved
	response := RiskResponse{
		Approved: true,
	}
	
	// Update daily traded amount
	err = updateDailyTradedAmount(tradeReq.UserID, dailyTraded+tradeReq.Amount)
	if err != nil {
		log.Printf("Failed to update daily traded amount: %v", err)
	}
	
	// Log risk event to Kafka
	logRiskEvent(tradeReq, "APPROVED", "")
	
	json.NewEncoder(w).Encode(response)
}

func getUserLimitsHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	
	vars := mux.Vars(r)
	userID := vars["user_id"]
	
	dailyLimit, err := getUserDailyLimit(userID)
	if err != nil {
		log.Printf("Failed to get user limits: %v", err)
		http.Error(w, "Failed to get user limits", http.StatusInternalServerError)
		return
	}
	
	dailyTraded, err := getDailyTradedAmount(userID)
	if err != nil {
		log.Printf("Failed to get daily traded amount: %v", err)
		http.Error(w, "Failed to get daily traded amount", http.StatusInternalServerError)
		return
	}
	
	response := UserLimits{
		UserID:      userID,
		DailyLimit:  dailyLimit,
		DailyTraded: dailyTraded,
		Remaining:   dailyLimit - dailyTraded,
	}
	
	json.NewEncoder(w).Encode(response)
}

func getUserDailyLimit(userID string) (float64, error) {
	val, err := rdb.Get(ctx, "user:"+userID+":daily_limit").Result()
	if err == redis.Nil {
		// Default limit if not set
		return 10000.0, nil
	} else if err != nil {
		return 0, err
	}
	
	return strconv.ParseFloat(val, 64)
}

func getDailyTradedAmount(userID string) (float64, error) {
	today := time.Now().Format("2006-01-02")
	key := "user:"+userID+":traded:"+today
	
	val, err := rdb.Get(ctx, key).Result()
	if err == redis.Nil {
		return 0, nil
	} else if err != nil {
		return 0, err
	}
	
	return strconv.ParseFloat(val, 64)
}

func updateDailyTradedAmount(userID string, amount float64) error {
	today := time.Now().Format("2006-01-02")
	key := "user:"+userID+":traded:"+today
	
	// Set with 24h expiry
	return rdb.Set(ctx, key, amount, 24*time.Hour).Err()
}

func logRiskEvent(trade TradeRequest, decision string, reason string) {
	event := map[string]interface{}{
		"user_id":   trade.UserID,
		"symbol":    trade.Symbol,
		"action":    trade.Action,
		"amount":    trade.Amount,
		"price":     trade.Price,
		"decision":  decision,
		"reason":    reason,
		"timestamp": time.Now().Unix(),
	}
	
	eventBytes, _ := json.Marshal(event)
	err := kafkaWriter.WriteMessages(ctx, kafka.Message{
		Key:   []byte(trade.UserID),
		Value: eventBytes,
	})
	
	if err != nil {
		log.Printf("Failed to write to Kafka: %v", err)
	}
} 