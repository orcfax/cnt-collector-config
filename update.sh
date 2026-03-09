#!/bin/bash


. .env
# Show the contents of the .env file for logging purposes
cat .env

PAIRS=$(curl -s $FEEDS_URL | grep pair | awk '{print $2}' | cut -d\" -f2 | xargs)
echo pairs: $PAIRS

echo "Running Python script to generate configuration file..."
python -m src.cnt_collector_config.main

if [ $? -ne 0 ]; then
    echo "Error: Failed to run the Python script."
    exit 1
fi
echo "Python script executed successfully."

# Check if the output file exists
if [ -f "$GENERATED_CONFIG" ]; then
    echo "Output file $GENERATED_CONFIG exists."
else
    echo "Error: Output file $GENERATED_CONFIG does not exist."
    exit 1
fi
# Check if the output file is not empty
if [ -s "$GENERATED_CONFIG" ]; then
    echo "Output file $GENERATED_CONFIG is not empty."
else
    echo "Error: Output file $GENERATED_CONFIG is empty."
    exit 1
fi
# Check if the output file contains the expected content
for PAIR in $PAIRS; do
    if grep -q "$PAIR" "$GENERATED_CONFIG"; then
        echo "Output file $GENERATED_CONFIG contains the pair: $PAIR."
    else
        echo "Error: Output file $GENERATED_CONFIG does not contain the pair: $PAIR."
        exit 1
    fi
done
# Check if the output file is a valid python file
if python -m py_compile "$GENERATED_CONFIG" >/dev/null 2>&1; then
    echo "Output file $GENERATED_CONFIG is a valid Python file."
else
    echo "Error: Output file $GENERATED_CONFIG is not a valid Python file."
    exit 1
fi
#Check if the generated config file is the same as the current config file
if cmp -s "$GENERATED_CONFIG" "$CURRENT_CONFIG"; then
    echo "Generated config file is the same as the current config file."
else
    echo "Generated config file is different from the current config file."
    echo "Copying generated config file to current config file..."
    cp "$GENERATED_CONFIG" "$CURRENT_CONFIG"
    if [ $? -eq 0 ]; then
        echo "Current config file updated successfully."
    else
        echo "Error: Failed to update the current config file."
        exit 1
    fi
fi
