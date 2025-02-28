import random
import json
import os
import logging
import argparse

# Constants
DATA_DIR = "naming_data"
MASTER_FILE = "master_names.json"
CYCLES_FILE = "cycles_data.json"

# Set up logging
logging.basicConfig(filename='naming_generator.log', level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

def ensure_data_directory():
    """Create data directory if it doesn't exist."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

def load_naming_data():
    """Load all naming data from JSON files in the data directory."""
    namespaces = {}
    for file in os.listdir(DATA_DIR):
        if file.endswith(".json"):
            culture = file.split(".")[0].capitalize()
            file_path = os.path.join(DATA_DIR, file)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    namespaces[culture] = json.load(f)
            except json.JSONDecodeError as e:
                logging.error(f"Error decoding JSON for {file}: {e}")
                raise
    return namespaces

def load_or_initialize_master():
    """Load or create the master names file."""
    if os.path.exists(MASTER_FILE):
        with open(MASTER_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def load_or_initialize_cycles():
    """Load or create the cycles data file."""
    if os.path.exists(CYCLES_FILE):
        with open(CYCLES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"cycles": {}, "name_to_cycle": {}}

def save_cycles(cycles_data):
    """Save cycles data to file."""
    with open(CYCLES_FILE, "w", encoding="utf-8") as f:
        json.dump(cycles_data, f, indent=4, ensure_ascii=False)

def is_duplicate(name, master_names):
    """Check if a name already exists in the master list."""
    return name in master_names

def save_to_master(name, master_names):
    """Save a generated name to the master file."""
    master_names[name] = True
    with open(MASTER_FILE, "w", encoding="utf-8") as f:
        json.dump(master_names, f, indent=4, ensure_ascii=False)

def get_or_create_cycle_event(cycles_data, cycle_number, namespace):
    """Get or create an event for a specific cycle number."""
    cycles = cycles_data.get("cycles", {})
    cycle_key = str(cycle_number)

    if cycle_key not in cycles:
        cycles[cycle_key] = random.choice(namespace.get("events", ["Unnamed Cycle"]))
        cycles_data["cycles"] = cycles
        save_cycles(cycles_data)

    return cycles[cycle_key]

def generate_name(
    culture, namespaces, master_names, cycles_data, max_attempts=100, **kwargs
):
    """Generate a name based on culture-specific naming conventions."""
    namespace = namespaces.get(culture, {})
    if not namespace:
        raise ValueError(f"No naming data available for {culture}")

    if max_attempts <= 0:
        raise ValueError(f"Could not generate a unique name for {culture} after many attempts")

    # Default name generation logic for unhandled cultures
    if culture == "Constructs":
        full_name = random.choice(namespace.get("titles", ["Construct"]))
    else:
        cycle_number = random.randint(1, 998)
        cycle_event = kwargs.get("cycle_event") or get_or_create_cycle_event(cycles_data, cycle_number, namespace)

        if culture == "Unrooted":
            full_name = f"The {kwargs.get('mothertree', random.choice(namespace.get('mothertree', ['of ˈfilʃɛ'])))} {random.choice(namespace.get('name', ['ʒij']))} of {cycle_event}"
        elif culture == "Valain":
            full_name = " ".join([
                kwargs.get("titles", random.choice(namespace.get("titles", ["Alpha"]))),
                random.choice(namespace.get("name", ["kal"])),
                random.choice(namespace.get("traits", ["The Swift"])),
                kwargs.get("dominion", random.choice(namespace.get("dominion", ["Fire"])))
            ])
        elif culture == "Oonar":
            full_name = " ".join([
                kwargs.get("processes", random.choice(namespace.get("processes", ["autolysee"]))),
                random.choice(namespace.get("name", ["tu"]))
            ])
        elif culture == "Aumian":
            full_name = " ".join([
                kwargs.get("function", random.choice(namespace.get("function", ["Worker"]))),
                kwargs.get("heritage", random.choice(namespace.get("heritage", ["Descendant of Worker ˌgalpuʒˈvɑdɑl"]))),
                random.choice(namespace.get("name", ["tup"]))
            ])
        elif culture == "DriftersSky":
            full_name = " ".join([
                kwargs.get("autotroph", random.choice(namespace.get("autotroph", ["Mosi"]))),
                random.choice(namespace.get("name", ["ˈmɑmir"])),
                random.choice(namespace.get("character", ["The free"]))
            ])
        elif culture == "DriftersSea":
            full_name = " ".join([
                kwargs.get("depth", random.choice(namespace.get("depth", ["surface"]))),
                random.choice(namespace.get("name", ["ken"])),
                kwargs.get("clan_names", random.choice(namespace.get("clan_names", ["Rafters"])))
            ])
        elif culture == "DriftersLand":
            full_name = " ".join([
                kwargs.get("depth", random.choice(namespace.get("title", ["surface"]))),
                random.choice(namespace.get("name", ["ken"])),
                kwargs.get("clan_names", random.choice(namespace.get("character", ["Rafters"])))
            ])
        elif culture == "Norian":
            full_name = " ".join([
                kwargs.get("depth", random.choice(namespace.get("generation", ["lost"]))),
                random.choice(namespace.get("name", ["Astaj"])),
                kwargs.get("family", random.choice(namespace.get("family", ["Root"])))
            ])
        elif culture == "Napa":
            full_name = " - ".join([
                random.choice(namespace.get("name", ["Kelvin"])),
                kwargs.get("homestead", random.choice(namespace.get("homestead", ["Stonecroft"])))
            ])
        elif culture == "Pi":
            full_name = " ".join([
                random.choice(namespace.get("something_cool", ["Creative Juice"])),
                random.choice(namespace.get("cool_name", ["tav"]))
            ])
        else:
            raise ValueError(f"Unsupported culture: {culture}")

    # Avoid duplicates
    if is_duplicate(full_name, master_names):
        return generate_name(culture, namespaces, master_names, cycles_data, max_attempts - 1, **kwargs)

    save_to_master(full_name, master_names)
    return full_name

def generate_batch(culture, count, **kwargs):
    """Generate and save a batch of names for a specific culture."""
    ensure_data_directory()
    namespaces = load_naming_data()
    master_names = load_or_initialize_master()
    cycles_data = load_or_initialize_cycles()

    generated_names = []
    file_name = f"{culture}_names.txt"

    for i in range(count):
        try:
            name = generate_name(culture, namespaces, master_names, cycles_data, **kwargs)
            generated_names.append(name)
            logging.info(f"Generated name {i+1}/{count} for {culture}: {name}")
        except ValueError as e:
            logging.error(f"Error generating name: {e}")
            break

    if generated_names:
        with open(file_name, "w", encoding="utf-8") as f:
            for name in generated_names:
                f.write(name + "\n")

    print(f"\nCompleted generating names for {culture} in {file_name}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate names for different cultures.")
    parser.add_argument("--culture", required=True, help="The culture for which to generate names.")
    parser.add_argument("--count", type=int, default=10, help="Number of names to generate.")
    parser.add_argument("--family", help="Lock in a specific family name (e.g., 'Treestump').")
    parser.add_argument("--homestead", help="Lock in a specific homestead name (e.g., 'Willowbend').")
    parser.add_argument("--mothertree", help="Lock in a specific mothertree name.")
    parser.add_argument("--cycle_event", help="Lock in a specific cycle event.")
    parser.add_argument("--titles", help="Lock in a specific title.")
    parser.add_argument("--dominion", help="Lock in a specific dominion.")
    parser.add_argument("--processes", help="Lock in a specific process.")
    parser.add_argument("--function", help="Lock in a specific function.")
    parser.add_argument("--heritage", help="Lock in a specific heritage.")
    parser.add_argument("--autotroph", help="Lock in a specific autotroph.")
    parser.add_argument("--depth", help="Lock in a specific depth.")
    parser.add_argument("--clan_names", help="Lock in a specific clan name.")
    args = parser.parse_args()

    generate_batch(args.culture, args.count, **vars(args))
