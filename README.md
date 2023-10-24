# Bot for calculating debts in group of people
## 1. Description
### 1.1 General information

This bot is designed to simplify calculations when spending together on trips, events, etc. 
It allows you not to count every time who owes whom and how much, and also eliminates the need to 
transfer money every time after each expenditure.

It is easy to use - add to the chat, register and start adding payments. At the end, the bot itself
will calculate and display who should transfer to whom and how much to pay off debts. 
It will take into account situations with “complex” debt (for example John -> Bob -> Andrew) 
and will reduce the amount of money transferred, bypassing people in the middle.

### 1.2 Terms
Describing how the bot works, the following terms will be used:

- Chat - group chat in which the bot was added as the administrator.
- Group of payments (or just group) - a separate group of expenses (for example trip to the mountains, barbecue ets.).
- Balance - total user spending balance. Positive - the user is owed money, negative - user owes money.
- Payment - one common expense within the group, divided among several people. Each payment changes the balance of its participants.
- Registration  - adding a user to a group.

### 1.3 Algorithm
The bot will try to convert user balances into final debts in such a way that:

1. Reduce the number of money transfers between users (if John owes Bob, and Bob owes Andrew, then John can transfer to Andrew directly).
2. Reduce the amount of money transferred.

The end result will be that each user either receives or transfers money as part of paying off debts.
