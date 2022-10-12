from aiogram.utils.callback_data import CallbackData

# Different callback interfaces to use in different keyboards
payer_cb = CallbackData("payer", "payer")
debtor_cb = CallbackData("debtor", "debtor")
all_cb = CallbackData("all", "all")
delete_cb = CallbackData("payment", "payment")
back_pay = CallbackData("back_payers")
