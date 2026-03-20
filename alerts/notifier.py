"""
alerts/notifier.py

Console and optional email alerting for flagged anomalies.
Fires on every flagged bar with structured output and a mandatory disclaimer.
"""

import smtplib
from email.mime.text import MIMEText
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import Config

DISCLAIMER = (
    "DISCLAIMER: This alert represents a statistical deviation from historical patterns "
    "detected by an automated ML system. It does not constitute financial advice, a "
    "trading signal, or a prediction of future price movement. Do not make investment "
    "decisions based on this output."
)


def fire_alert(ticker: str, timestamp: str, scores: dict, config: Config) -> None:
    """Fire an anomaly alert to console and optionally via email.

    Always prints a structured alert to stdout.
    If email is enabled in config, sends via smtplib TLS.

    Args:
        ticker: Stock ticker symbol (e.g. "AAPL").
        timestamp: ISO 8601 timestamp string of the anomalous bar.
        scores: Dictionary with keys:
            - ensemble_score (float)
            - zscore (float)
            - if_score (float)
            - lstm_score (float)
        config: Config instance with email settings.
    """
    ensemble_score = scores.get("ensemble_score", 0.0)
    zscore = scores.get("zscore", 0.0)
    if_score = scores.get("if_score", 0.0)
    lstm_score = scores.get("lstm_score", 0.0)

    # ── Console alert ──────────────────────────────────────────────
    console_msg = (
        f"[ANOMALY] {timestamp} | {ticker} | "
        f"ensemble={ensemble_score:.3f} | "
        f"z={zscore:.3f} | if={if_score:.3f} | lstm={lstm_score:.3f}"
    )
    print(console_msg)
    print(DISCLAIMER)
    print()  # blank line separator

    # ── Email alert (optional) ─────────────────────────────────────
    if config.ALERT_EMAIL_ENABLED:
        _send_email_alert(ticker, timestamp, scores, config)


def _send_email_alert(
    ticker: str, timestamp: str, scores: dict, config: Config
) -> None:
    """Send a plain-text anomaly alert email via SMTP TLS.

    Args:
        ticker: Stock ticker symbol.
        timestamp: ISO 8601 timestamp string.
        scores: Dictionary with ensemble_score, zscore, if_score, lstm_score.
        config: Config instance with SMTP settings.
    """
    ensemble_score = scores.get("ensemble_score", 0.0)
    zscore = scores.get("zscore", 0.0)
    if_score = scores.get("if_score", 0.0)
    lstm_score = scores.get("lstm_score", 0.0)

    subject = f"[ANOMALY ALERT] {ticker} @ {timestamp}"

    body = (
        f"Anomaly detected for {ticker} at {timestamp}\n"
        f"\n"
        f"Scores:\n"
        f"  Ensemble : {ensemble_score:.3f}\n"
        f"  Z-Score  : {zscore:.3f}\n"
        f"  Iso Forest: {if_score:.3f}\n"
        f"  LSTM     : {lstm_score:.3f}\n"
        f"\n"
        f"{DISCLAIMER}\n"
    )

    msg = MIMEText(body, "plain")
    msg["Subject"] = subject
    msg["From"] = config.ALERT_EMAIL_SENDER
    msg["To"] = config.ALERT_EMAIL_RECIPIENT

    try:
        with smtplib.SMTP(
            config.ALERT_EMAIL_SMTP_HOST, config.ALERT_EMAIL_SMTP_PORT
        ) as server:
            server.starttls()
            server.login(config.ALERT_EMAIL_SENDER, os.environ.get("EMAIL_PASSWORD", ""))
            server.sendmail(
                config.ALERT_EMAIL_SENDER,
                config.ALERT_EMAIL_RECIPIENT,
                msg.as_string(),
            )
        print(f"[EMAIL SENT] Alert emailed to {config.ALERT_EMAIL_RECIPIENT}")
    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send alert email: {e}")
