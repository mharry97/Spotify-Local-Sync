from src.database import get_coverage_stats
from src.fuzzy_match import find_all_potential_matches
from src.local_scan import sync_local
from src.spotify_scan import sync_spotify

# Present user with options
def show_menu():
  print("\n--- Music Library Matcher ---")
  print("1. Full Sync")
  print("2. Sync Local Library to Database")
  print("3. Sync Spotify Saved to Database")
  print("4. Get Coverage Stats")
  print("5. Scan For Potential Matches")
  print("6. Exit")
  return input("Choose an option: ")

def continue_option():
  resp = input("\nWould you like to perform another action? (y/n)").lower()
  if resp == 'y':
    print("Exiting. Goodbye!")
    return True
  elif resp == 'n':
    return False
  else:
    print("Invalid choice. Please enter 'y' or 'n'.")

# Prettify the stats
def coverage_pretty(stats):
  print("\n--- Coverage Stats ---")
  print(f"Spotify Saved Songs: {stats['total']}")
  print(f"Matched Spotify Songs: {stats['matched']}")
  print(f"Unmatched Spotify Songs: {stats['unmatched']}")
  print(f"Coverage: {stats['coverage']}%")

def main():
  # Main runner
  while True:
    choice = show_menu()
    if choice == '1':
      sync_spotify()
      sync_local()
      coverage_pretty(get_coverage_stats())
    elif choice == '2':
      sync_local()
    elif choice == '3':
      sync_spotify()
    elif choice == '4':
      coverage_pretty(get_coverage_stats())
    elif choice == '5':
      find_all_potential_matches()
    elif choice == '6':
      print("Exiting. Goodbye!")
      break
    else:
      print("Invalid choice. Please try again.")
      continue

    # After any valid action ask the user if they want to continue
    if not continue_option():
      break


if __name__ == "__main__":
  main()
