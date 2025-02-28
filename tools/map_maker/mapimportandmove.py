import os
import msvcrt
import time
import json
import math

class Building:
    def __init__(self, id, type, specific_type, coords, floors=1):
        self.id = id
        self.type = type
        self.specific_type = specific_type
        self.coords = coords  # List of coordinate pairs
        self.floors = floors
        self.symbol = self.get_symbol()
        
    def get_symbol(self):
        # Choose a symbol based on building type
        if self.type == "residential":
            if "Noble" in self.specific_type or "Manor" in self.specific_type:
                return "M"  # Manor/Noble houses
            elif "Farmhouse" in self.specific_type:
                return "F"  # Farmhouse
            elif "Townhouse" in self.specific_type:
                return "T"  # Townhouse
            elif "Communal" in self.specific_type or "Longhouse" in self.specific_type:
                return "C"  # Communal buildings
            else:
                return "H"  # Generic house
        elif self.type == "other":
            if "Bell" in self.specific_type:
                return "B"  # Bell tower
            elif "Watchtower" in self.specific_type:
                return "W"  # Watchtower
            elif "Chapel" in self.specific_type:
                return "+"  # Religious buildings
            elif "Hall" in self.specific_type:
                return "G"  # Government/Town Hall
            elif "Fortification" in self.specific_type:
                return "#"  # Fortifications
            else:
                return "O"  # Other structures
        else:
            return "?"  # Unknown

    def is_point_inside(self, x, y):
        """Check if point is within building coordinates"""
        # Simple bounding box check
        x_coords = [p[0] for p in self.coords]
        y_coords = [p[1] for p in self.coords]
        return (min(x_coords) <= x <= max(x_coords) and 
                min(y_coords) <= y <= max(y_coords))

class Character:
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y
        self.symbol = "@"

    def move(self, direction, steps=1):
        if direction == 'north':
            self.y += steps
        elif direction == 'south':
            self.y -= steps
        elif direction == 'east':
            self.x += steps
        elif direction == 'west':
            self.x -= steps

class Map:
    def __init__(self, width=60, height=30, geojson_file=None):
        self.width = width
        self.height = height
        self.buildings = []
        self.character = Character()
        
        # Calculate center position for character start
        self.min_x = float('inf')
        self.max_x = float('-inf')
        self.min_y = float('inf')
        self.max_y = float('-inf')
        
        # Load buildings from GeoJSON if provided
        if geojson_file:
            self.load_geojson(geojson_file)
            
            # Position character near the center of the map
            center_x = (self.min_x + self.max_x) / 2
            center_y = (self.min_y + self.max_y) / 2
            self.character.x = center_x
            self.character.y = center_y
            
            # Scale factors for display
            self.scale_x = width / ((self.max_x - self.min_x) * 1.1)
            self.scale_y = height / ((self.max_y - self.min_y) * 1.1)
            
    def load_geojson(self, filename):
        """Load buildings from GeoJSON file"""
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
                
            for feature in data['features']:
                props = feature['properties']
                geom = feature['geometry']
                
                if geom['type'] == 'Polygon':
                    coords = []
                    for point in geom['coordinates'][0]:
                        x, y = point
                        coords.append((x, y))
                        
                        # Update map boundaries
                        self.min_x = min(self.min_x, x)
                        self.max_x = max(self.max_x, x)
                        self.min_y = min(self.min_y, y)
                        self.max_y = max(self.max_y, y)
                    
                    # Create building with proper attributes
                    building = Building(
                        id=props.get('id', 'unknown'),
                        type=props.get('type', 'unknown'),
                        specific_type=props.get('specific_type', 'unknown'),
                        coords=coords,
                        floors=int(props.get('floors', 1)) if props.get('floors') else 1
                    )
                    self.buildings.append(building)
                    
            print(f"Loaded {len(self.buildings)} buildings from {filename}")
            
        except Exception as e:
            print(f"Error loading GeoJSON file: {e}")

    def get_building_at_position(self, x, y):
        """Find building at the given coordinates"""
        for building in self.buildings:
            if building.is_point_inside(x, y):
                return building
        return None

    def display(self):
        # Clear screen (Windows)
        os.system('cls')
        
        # Create a grid representation of the map
        grid = [[' ' for _ in range(self.width)] for _ in range(self.height)]
        
        # Plot buildings on the grid
        for building in self.buildings:
            # Get center point of building
            x_coords = [p[0] for p in building.coords]
            y_coords = [p[1] for p in building.coords]
            center_x = sum(x_coords) / len(x_coords)
            center_y = sum(y_coords) / len(y_coords)
            
            # Convert to grid coordinates
            grid_x = int((center_x - self.min_x) * self.scale_x)
            grid_y = int((center_y - self.min_y) * self.scale_y)
            
            # Make sure it's within bounds
            if 0 <= grid_x < self.width and 0 <= grid_y < self.height:
                grid[grid_y][grid_x] = building.symbol
        
        # Plot character
        char_grid_x = int((self.character.x - self.min_x) * self.scale_x)
        char_grid_y = int((self.character.y - self.min_y) * self.scale_y)
        
        if 0 <= char_grid_x < self.width and 0 <= char_grid_y < self.height:
            grid[char_grid_y][char_grid_x] = self.character.symbol
        
        # Display the map
        print("\nCitadel of Utaia - ASCII Map Explorer")
        print("-------------------------------------")
        print("Character position: ({:.6f}, {:.6f})".format(self.character.x, self.character.y))
        
        # Draw the grid with border
        print("+" + "-" * self.width + "+")
        for row in grid:
            print("|" + ''.join(row) + "|")
        print("+" + "-" * self.width + "+")
        
        # Check if character is inside a building
        building = self.get_building_at_position(self.character.x, self.character.y)
        if building:
            print(f"\nYou are in: {building.specific_type} ({building.id})")
            print(f"Type: {building.type}, Floors: {building.floors}")
        else:
            print("\nYou are outdoors in the Citadel of Utaia")
            
        print("\nLegend:")
        print("@ - You   H - House   M - Manor/Noble   F - Farmhouse")
        print("T - Townhouse   C - Communal   # - Fortification   + - Chapel")
        print("B - Bell Tower   W - Watchtower   G - Government   O - Other")

    def process_command(self, command):
        # Use a simpler approach instead of NLTK tokenization
        tokens = command.lower().split()
        
        if 'move' in tokens:
            direction_index = tokens.index('move') + 1
            if direction_index < len(tokens):
                direction = tokens[direction_index]
                steps = 1
                if direction_index + 1 < len(tokens) and tokens[direction_index + 1].isdigit():
                    steps = int(tokens[direction_index + 1])
                self.character.move(direction, steps * 0.0001)  # Scale step size to match coordinate system
                
        # Simple command shortcuts
        elif command == 'n' or command == 'north':
            self.character.move('north', 0.0001)
        elif command == 's' or command == 'south':
            self.character.move('south', 0.0001)
        elif command == 'e' or command == 'east':
            self.character.move('east', 0.0001)
        elif command == 'w' or command == 'west':
            self.character.move('west', 0.0001)
        elif command == 'info':
            # Show more detailed info about current location
            building = self.get_building_at_position(self.character.x, self.character.y)
            if building:
                print(f"\nDetailed information about: {building.specific_type}")
                print(f"Building ID: {building.id}")
                print(f"Type: {building.type}")
                print(f"Floors: {building.floors}")
                print("\nPress any key to continue...")
                msvcrt.getch()

def get_key():
    """Get a key press and return the corresponding command."""
    print("Controls: Arrow keys to move, 'Esc' to exit, 'i' for info, or type a command")
    print("Enter command (or press an arrow key): ", end='', flush=True)
    
    # Check for a keypress
    key = msvcrt.getch()
    
    # Check for arrow keys (special keys start with b'\xe0')
    if key == b'\xe0':
        arrow_key = msvcrt.getch()
        if arrow_key == b'H':  # Up arrow
            print("↑ (up)")
            return "move north 1"
        elif arrow_key == b'P':  # Down arrow
            print("↓ (down)")
            return "move south 1"
        elif arrow_key == b'K':  # Left arrow
            print("← (left)")
            return "move west 1"
        elif arrow_key == b'M':  # Right arrow
            print("→ (right)")
            return "move east 1"
    elif key == b'\x1b':  # Esc key
        print("exit")
        return "exit"
    else:
        # Convert the byte to a string
        try:
            char = key.decode('utf-8')
            # Handle single-character commands
            if char == 'w':
                return "move north 1"
            elif char == 's':
                return "move south 1"
            elif char == 'a':
                return "move west 1"
            elif char == 'd':
                return "move east 1"
            elif char == 'q':
                return "exit"
            elif char == 'i':
                return "info"
        except:
            pass
            
    # If no special key was processed, read a regular command
    print("\nEnter full command: ", end='')
    command = input().strip().lower()
    return command

def main():
    # Ask for the GeoJSON file path
    geojson_file = "buildings_citadel_of_utaia.geojson_fixed.geojson_poly.geojson"
    
    # Create the map with GeoJSON data
    city_map = Map(geojson_file=geojson_file)
    
    print("Welcome to the Citadel of Utaia Explorer!")
    print("Use arrow keys, WASD, or 'move [direction] [steps]' commands to navigate.")
    print("Press 'i' for detailed information about your current location.")
    print("Press Esc or 'q' to exit.")
    time.sleep(2)  # Give user time to read instructions
    
    while True:
        city_map.display()
        command = get_key()
        if command == 'exit':
            break
        city_map.process_command(command)

if __name__ == "__main__":
    main()