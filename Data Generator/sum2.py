numbers = []
target = int(input("Enter your target number: "))

print(f"Enter up to 5 different numbers with at least two of them equalling your target. Press Enter with no input to stop.")

while len(numbers) < 5:
    user_input = input(f"Enter number {len(numbers) + 1}: ").strip()

    if user_input == "":
        break

    try:
        number = int(user_input)
    except ValueError:
        print("Please enter a valid number.")
        continue

    if number in numbers:
        print("Please enter a different number.")
        continue

    numbers.append(number)

print("Your list:", numbers)

while True:
    if len(numbers) < 2:
        print("Not enough numbers to sum to the target.")
        break

    found = False
    for i in range(len(numbers)):
        for j in range(i + 1, len(numbers)):
            if numbers[i] + numbers[j] == target:
                print(f"Found a pair: {numbers[i]} + {numbers[j]} = {target}")
                found = True
                break
        if found:
            break

    if not found:
        print("No pairs found that sum to the target.")
    break