from machine import Pin, ADC
import asyncio
import gc

# Run the garbage collector to free up memory.
gc.collect()


# ==================================================
# Pin Assignments and Global Variables
# ==================================================
# ADC for MIC
mic = ADC(Pin(34), atten=ADC.ATTN_11DB)
micValueMax = 0  # The global variable to store the amplitude. It will be reduced slowly.
inAudioMode = True  # Set to True to enable the audio mode.


# ==================================================
# asyncio Functions
# ==================================================
# Function: ADC for MIC
async def mic_handler():
    global micValueMax
    dymamic_range = 1  # Initialize with a small value
    decay_rate = 0.95  # Adjust this value to change the rate of decay
    while True:
        if inAudioMode:
            # Get 32 sound samples
            samples = []
            for i in range(32):
                samples.append(mic.read_u16())

            # Calculate the amplitude.
            micValue = max(samples) - min(samples)
            print(f"MIC: {micValue}")

            # Update the dynamic range if necessary
            if micValue > dymamic_range:
                dymamic_range = micValue
            # Else, reduce the dynamic range slowly.
            else:
                dymamic_range = max(int(dymamic_range - 10), 1)

            # Remap the value according to the dynamic range
            micValue = int((micValue / dymamic_range) * 65535)

            # Update the MIC value to the global variable.
            if micValue > micValueMax:
                micValueMax = micValue
            # Else, reduce the MIC value slowly.
            else:
                micValueMax = max(int(micValueMax * decay_rate), 0)

            # Print the MIC value
            print(f"MIC Max: {micValueMax}")

        await asyncio.sleep(0.005)


# ==================================================
# Main
# ==================================================
# For asyncio, see: https://github.com/orgs/micropython/discussions/10933
# and also see: https://docs.micropython.org/en/latest/library/asyncio.html
async def main():
    task_mic = asyncio.create_task(mic_handler())
    await asyncio.gather(task_mic)

while True:
    asyncio.run(main())
    pass
