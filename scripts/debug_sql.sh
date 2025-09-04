#!/bin/bash
# Mobile Sales SQL Debug Helper Script

LOG_FILE="/var/log/apache2/mobile_sales_sql.log"
ANALYZER="/var/www/html/Mobile_Sales/sql_log_analyzer.py"

echo "Mobile Sales SQL Debug Helper"
echo "=============================="

case "$1" in
    "live")
        echo "Monitoring SQL log in real-time (Ctrl+C to stop)..."
        tail -f "$LOG_FILE"
        ;;
    "stats")
        echo "SQL Log Statistics:"
        python3 "$ANALYZER" --stats
        ;;
    "errors")
        echo "SQL Errors:"
        python3 "$ANALYZER" --errors
        ;;
    "select")
        echo "SELECT queries:"
        python3 "$ANALYZER" --operation SELECT
        ;;
    "clear")
        echo "Clearing SQL log..."
        > "$LOG_FILE"
        echo "Log cleared."
        ;;
    "last")
        echo "Last 20 SQL operations:"
        tail -20 "$LOG_FILE"
        ;;
    "help"|"")
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  live     - Monitor SQL log in real-time"
        echo "  stats    - Show SQL statistics"
        echo "  errors   - Show only SQL errors"
        echo "  select   - Show only SELECT queries"
        echo "  clear    - Clear the SQL log"
        echo "  last     - Show last 20 operations"
        echo "  help     - Show this help"
        echo ""
        echo "Examples:"
        echo "  $0 live"
        echo "  $0 stats"
        echo "  $0 errors"
        ;;
    *)
        echo "Unknown command: $1"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac