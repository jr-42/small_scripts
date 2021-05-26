def sievePrimes(maximum):
    primes = dict.fromkeys(range(3,maximum+1,2),True)
    sieveList = [2]
    for num in sorted(primes):
        if primes[num] == True:
            sieveList.append(num)
            j = num ** 2
            while j < maximum:
                if j in primes:
                    primes[j] = False
                j += num
    return(sieveList)

x = sievePrimes(50000000)
print(x)