import os
import asyncio
import logging
from datetime import datetime
from telethon import TelegramClient, errors

logging.basicConfig(filename='bot.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

api_id1 = input('api1: ')
api_hash1 = input('hash1: ')
session_name1 = 'anon1'

current_time1 = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
session_file1 = f'{session_name1}_{current_time1}.session'

client1 = TelegramClient(session_file1, api_id1, api_hash1)

api_id2 = input('api2: ')
api_hash2 = input('hash2: ')
session_name2 = 'anon2'

current_time2 = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
session_file2 = f'{session_name2}_{current_time2}.session'

client2 = TelegramClient(session_file2, api_id2, api_hash2)

total_requests1 = 0
success_count1 = 0
failure_count1 = 0

total_requests2 = 0
success_count2 = 0
failure_count2 = 0

async def send_start_commands(client, bot_username, start_param, repeat_count, total_requests, success_count, failure_count):
    tasks = []
    for _ in range(repeat_count):
        task = client.send_message(bot_username, f'/start {start_param}')
        tasks.append(task)

    try:
        await asyncio.gather(*tasks)
        logging.info(f"Sent /start message to: {bot_username} with start param: {start_param} {repeat_count} times")
        success_count += 1
    except errors.FloodWaitError as e:
        logging.error(f"Flood wait error: need to wait for {e.seconds} seconds")
        await asyncio.sleep(e.seconds)
        await send_start_commands(client, bot_username, start_param, repeat_count, total_requests, success_count, failure_count)
    except Exception as e:
        logging.error(f"Error while sending message: {e}")
        failure_count += 1

    total_requests += repeat_count

async def authenticate(client):
    await client.start()
    me = await client.get_me()
    logging.info(f"Welcome, {me.first_name}!")
    logging.info("Authentication successful.")

async def process_account(client, total_requests, success_count, failure_count, account_name):
    await authenticate(client)

    channel_url = 'https://t.me/TONAirdropHunting'
    if channel_url.startswith('https://t.me/'):
        channel_username = channel_url.split('/')[-1]
    else:
        channel_username = channel_url

    try:
        channel = await client.get_entity(channel_username)
        async for message in client.iter_messages(channel, limit=2):
            if message.message and 'New Free #TON #Giveaway 👇' in message.message:
                if message.buttons:
                    urls = []
                    for row in message.buttons:
                        for button in row:
                            if button.url:
                                urls.append(button.url)

                    repeat_count = 100
                    if urls:
                        sem = asyncio.Semaphore(10)
                        async with sem:
                            for url in urls:
                                bot_username = url.split('/')[-1].split('?')[0]
                                start_param = url.split('start=')[-1] if 'start=' in url else ''
                                try:
                                    history = await client.get_messages(bot_username, limit=1)
                                    if not history or not history[0].message == f'/start {start_param}':
                                        await asyncio.gather(
                                            send_start_commands(client, bot_username, start_param, repeat_count, total_requests, success_count, failure_count),
                                            send_start_commands(client, bot_username, start_param, repeat_count, total_requests, success_count, failure_count)
                                        )
                                except Exception as e:
                                    logging.error(f"Error while checking message history or sending message: {e}")

        remaining_time = 7200
        while remaining_time > 0:
            logging.info(f"Waiting for {remaining_time // 3600} hours and {(remaining_time % 3600) // 60} minutes")
            await asyncio.sleep(60)
            remaining_time -= 60

        logging.info("Finished processing links. Now waiting for two hours before proceeding.")
    except errors.FloodWaitError as e:
        logging.error(f"Flood wait error: need to wait for {e.seconds} seconds")
        await asyncio.sleep(e.seconds)
        return
    except Exception as e:
        logging.error(f"Error while fetching messages: {e}")
        return

    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    results_file = f'results_{account_name}_{current_time}.txt'

    with open(results_file, 'w') as file:
        file.write(f"Total requests: {total_requests}\n")
        file.write(f"Successes: {success_count}\n")
        file.write(f"Failures: {failure_count}\n")

    logging.info(f"Results written to file {results_file}.")

    print(f"Script has finished running for {account_name}.")

async def main():
    await asyncio.gather(
        process_account(client1, total_requests1, success_count1, failure_count1, "account1"),
        process_account(client2, total_requests2, success_count2, failure_count2, "account2")
    )

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
