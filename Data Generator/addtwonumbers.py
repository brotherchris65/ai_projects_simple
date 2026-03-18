first = [3,6,1,8,4]
second = [5,2,7,9]

first = int("".join(map(str,first[::-1])))
second = int("".join(map(str,second[::-1])))
print(first + second)

