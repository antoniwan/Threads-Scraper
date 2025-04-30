from threads_interface import ThreadsInterface

# Initialize the interface
ti = ThreadsInterface()

# Enter your Threads username (without the @)
username = "antoniwan777"  # <-- Replace with your username

# Get your user ID
user_id = ti.retrieve_user_id(username)
print(f"User ID: {user_id}")

# Fetch your profile details
profile = ti.retrieve_user(user_id)
print("Profile:", profile)

# Fetch your threads (posts)
threads = ti.retrieve_user_threads(user_id)
print("Threads:", threads)

# Fetch your replies
replies = ti.retrieve_user_replies(user_id)
print("Replies:", replies)

# Save the data to files
ti.save_data_to_json(profile, "my_profile.json")
ti.save_data_to_json(threads, "my_threads.json")
ti.save_data_to_json(replies, "my_replies.json")
ti.save_data_to_csv(threads, "my_threads.csv")
ti.save_data_to_csv(replies, "my_replies.csv")