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
