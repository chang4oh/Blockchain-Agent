from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal

# Create your models here.

class UserSettings(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='settings')
    risk_percentage = models.DecimalField(
        max_digits=4, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01')), MaxValueValidator(100)],
        default=1.00,
        help_text="Risk percentage per trade (0.01-100)"
    )
    max_trades_per_day = models.PositiveIntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        help_text="Maximum number of trades allowed per day"
    )
    default_leverage = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        help_text="Default leverage for trades"
    )
    preferred_market = models.CharField(
        max_length=10,
        choices=[('SPOT', 'Spot'), ('FUTURES', 'Futures')],
        default='SPOT'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "User Settings"

    def __str__(self):
        return f"Settings for {self.user.username}"

class TradeLog(models.Model):
    TRADE_TYPES = [
        ('LONG', 'Long'),
        ('SHORT', 'Short'),
    ]

    TRADE_STATUS = [
        ('OPEN', 'Open'),
        ('CLOSED', 'Closed'),
        ('CANCELLED', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trades')
    symbol = models.CharField(max_length=20)
    trade_type = models.CharField(max_length=5, choices=TRADE_TYPES)
    entry_price = models.DecimalField(max_digits=20, decimal_places=8)
    exit_price = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    position_size = models.DecimalField(max_digits=20, decimal_places=8)
    stop_loss = models.DecimalField(max_digits=20, decimal_places=8)
    take_profit = models.DecimalField(max_digits=20, decimal_places=8)
    leverage = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=10, choices=TRADE_STATUS, default='OPEN')
    pnl = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    pnl_percentage = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.symbol} {self.trade_type} by {self.user.username}"

    def calculate_pnl(self):
        if self.status == 'CLOSED' and self.exit_price:
            if self.trade_type == 'LONG':
                pnl = (float(self.exit_price) - float(self.entry_price)) * float(self.position_size) * self.leverage
            else:  # SHORT
                pnl = (float(self.entry_price) - float(self.exit_price)) * float(self.position_size) * self.leverage
            
            self.pnl = Decimal(str(pnl))
            self.pnl_percentage = Decimal(str((pnl / (float(self.entry_price) * float(self.position_size))) * 100))

class CryptoPriceData(models.Model):
    symbol = models.CharField(max_length=20)
    timestamp = models.DateTimeField()
    open_price = models.DecimalField(max_digits=20, decimal_places=8)
    high_price = models.DecimalField(max_digits=20, decimal_places=8)
    low_price = models.DecimalField(max_digits=20, decimal_places=8)
    close_price = models.DecimalField(max_digits=20, decimal_places=8)
    volume = models.DecimalField(max_digits=30, decimal_places=8)
    
    class Meta:
        unique_together = ('symbol', 'timestamp')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['symbol', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.symbol} at {self.timestamp}"

class PricePrediction(models.Model):
    TIMEFRAME_CHOICES = [
        ('1h', '1 Hour'),
        ('4h', '4 Hours'),
        ('1d', '1 Day'),
        ('3d', '3 Days'),
        ('7d', '7 Days'),
    ]
    
    CONFIDENCE_LEVELS = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
    ]
    
    symbol = models.CharField(max_length=20)
    prediction_timestamp = models.DateTimeField(auto_now_add=True)
    target_timestamp = models.DateTimeField()
    timeframe = models.CharField(max_length=2, choices=TIMEFRAME_CHOICES)
    predicted_price = models.DecimalField(max_digits=20, decimal_places=8)
    confidence_level = models.CharField(max_length=6, choices=CONFIDENCE_LEVELS)
    confidence_score = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)])
    model_version = models.CharField(max_length=50)
    actual_price = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    prediction_error = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    class Meta:
        ordering = ['-prediction_timestamp']
        indexes = [
            models.Index(fields=['symbol', 'target_timestamp']),
        ]
    
    def __str__(self):
        return f"{self.symbol} prediction for {self.target_timestamp}"
    
    def calculate_error(self):
        if self.actual_price:
            error_pct = abs((float(self.predicted_price) - float(self.actual_price)) / float(self.actual_price) * 100)
            self.prediction_error = Decimal(str(error_pct))
            return self.prediction_error
        return None

class ModelPerformanceLog(models.Model):
    model_version = models.CharField(max_length=50)
    symbol = models.CharField(max_length=20)
    timeframe = models.CharField(max_length=2, choices=PricePrediction.TIMEFRAME_CHOICES)
    evaluation_date = models.DateTimeField(auto_now_add=True)
    mean_absolute_error = models.DecimalField(max_digits=10, decimal_places=4)
    mean_squared_error = models.DecimalField(max_digits=10, decimal_places=4)
    r_squared = models.DecimalField(max_digits=5, decimal_places=4)
    sample_size = models.PositiveIntegerField()
    
    class Meta:
        ordering = ['-evaluation_date']
    
    def __str__(self):
        return f"{self.model_version} performance for {self.symbol} ({self.timeframe})"
