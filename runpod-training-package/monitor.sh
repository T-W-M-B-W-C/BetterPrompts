#!/bin/bash
# Monitor training progress

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Function to get training progress
get_training_progress() {
    if [ -f "logs/training.log" ]; then
        # Extract latest epoch and step info
        epoch_info=$(grep -o "Epoch [0-9]*/[0-9]*" logs/training.log | tail -1)
        step_info=$(grep -o "Step [0-9]*/[0-9]*" logs/training.log | tail -1)
        loss_info=$(grep -o "loss: [0-9.]*" logs/training.log | tail -1)
        accuracy_info=$(grep -o "accuracy: [0-9.]*" logs/training.log | tail -1)
        
        echo -e "${BLUE}Training Progress:${NC}"
        [ -n "$epoch_info" ] && echo "  📊 $epoch_info"
        [ -n "$step_info" ] && echo "  🔄 $step_info"
        [ -n "$loss_info" ] && echo "  📉 Training $loss_info"
        [ -n "$accuracy_info" ] && echo "  🎯 Validation $accuracy_info"
    else
        echo -e "${YELLOW}No training log found yet...${NC}"
    fi
}

# Main monitoring loop
while true; do
    clear
    echo -e "${BLUE}=================================================${NC}"
    echo -e "${BLUE}   BetterPrompts Training Monitor${NC}"
    echo -e "${BLUE}   $(date)${NC}"
    echo -e "${BLUE}=================================================${NC}"
    
    # Check if training is running
    if tmux has-session -t training 2>/dev/null; then
        echo -e "\n${GREEN}✅ Training is running${NC}"
    else
        echo -e "\n${YELLOW}⚠️  Training session not found${NC}"
        
        # Check if results exist
        if ls results/*.tar.gz 2>/dev/null | head -1 > /dev/null; then
            echo -e "${GREEN}✅ Training complete! Results available in results/${NC}"
            echo -e "\nDownload with:"
            echo -e "${YELLOW}scp -P 18733 root@$(hostname -I | awk '{print $1}'):/workspace/runpod-training-package/results/*.tar.gz ./${NC}"
            exit 0
        fi
    fi
    
    # GPU Status
    echo -e "\n${BLUE}🎮 GPU Status:${NC}"
    nvidia-smi --query-gpu=name,utilization.gpu,memory.used,memory.total,temperature.gpu --format=csv,noheader | \
        awk -F', ' '{printf "  GPU: %s\n  Utilization: %s\n  Memory: %s / %s\n  Temperature: %s\n", $1, $2, $3, $4, $5}'
    
    # Training Progress
    echo ""
    get_training_progress
    
    # Recent log entries
    if [ -f "logs/training.log" ]; then
        echo -e "\n${BLUE}📄 Recent logs:${NC}"
        tail -5 logs/training.log | sed 's/^/  /'
    fi
    
    # Instructions
    echo -e "\n${BLUE}Commands:${NC}"
    echo -e "  ${YELLOW}tmux attach -t training${NC} - Attach to training session"
    echo -e "  ${YELLOW}tail -f logs/training.log${NC} - Follow log file"
    echo -e "  ${YELLOW}Ctrl+C${NC} - Exit monitor"
    
    echo -e "\n${BLUE}Refreshing in 10 seconds...${NC}"
    sleep 10
done