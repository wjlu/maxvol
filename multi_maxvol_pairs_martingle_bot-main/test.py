
import math

'''
voting power(用户持有的资产价值多少个LON) =
    用户地址持有的LON +
    用户地址持有的xLON换算成LON (用户地址持有的xLON * LON质押在xLON合约中的数量 / xLON总量) +
    用户地址持有的uniswap ETH/LON LP token换算成LON ((用户地址持有的lp + 质押在第2, 3, 4期流动性挖矿奖励合约中的lp) * (LON在ETH/LON pool里的数量 / lp token总量)) +
    用户地址持有的sushiswap LON/USDT SLP token换算成LON ((用户地址持有的slp + 质押在第2, 3, 4期流动性挖矿奖励合约中的slp) * (LON在LON/USDT pool里的数量 / slp token总量)) +
    用户地址在第2, 3, 4期流动性挖矿合约里未领取的LON挖矿奖励(uniswap staking contracts + sushiswap staking contracts共六个合约)



uniswap 中 ethlon的lp  holder   https://etherscan.io/token/0x7924a818013f39cf800f5589ff1f1f0def54f31f#balances
sushi  https://etherscan.io/token/0x55d31f68975e446a40a2d02ffa4b0e1bfb233c2f#balances
'''

'''
0x57b3c68caf0ebea2d9173bdb013655fd8da31aa4  地址持有的xlon 4700.6216个 ，lon 0个   = 5,984.36135896
pxlon 有  ？？？
https://etherscan.io/token/0x7924a818013f39cf800f5589ff1f1f0def54f31f#balances 

没有  uniswap / sushiswap lp 

5,984.36135896 + 45988.36315463263 + 29.8  = 52,002.5245135926
'''
'''
"stakingRewardUniswap4": "0xb6bC1a713e4B11fa31480d31C825dCFd7e8FaBFD",
"stakingRewardSushiSwap4": "0x9648B119f442a3a096C0d5A1F8A0215B46dbb547",

0x57b3c68caf0ebea2d9173bdb013655fd8da31aa4

https://etherscan.io/address/0xb6bC1a713e4B11fa31480d31C825dCFd7e8FaBFD#readContract

https://etherscan.io/address/0x9648B119f442a3a096C0d5A1F8A0215B46dbb547#readContract

'''
dishu =  math.pow(10,18)

jiangli_4 = 1000000000000098050753/dishu
print(jiangli_4)
print(jiangli_4/87367.449597858816243475 *4017886)

meiyouqu_4 = 29800564356865522967 / dishu
print(meiyouqu_4)

print(f"shushi jiangli 0")

#  https://etherscan.io/address/0x539a67B6f9c3caD58f434CC12624b2d520BC03F8#readContract

# https://etherscan.io/address/0x74379CEC6a2c9Fde0537e9D9346222a724A278e4#readContract
print(f"第三期: 0")

# https://etherscan.io/address/0xc348314f74B043Ff79396e14116B6f19122D69f4#readContract
# https://etherscan.io/address/0x11520d501E10E2E02A2715C4A9d3F8aEb1b72A7A#readContract
print(f"第2期: 0")



#  0xfa480a017108063ed7a739bf8bbfcfd410b879a8

