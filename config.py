import dotenv
import os

dotenv.load_dotenv()


BOT_TOKEN = os.getenv('USEDELECTRONICS_BOT_TOKEN')

required_channel = "@Ethiousedelectronics"

admin_id = 6783509602

MAX_PHOTOS = 5

PRIVATE_STORAGE_CHANNEL_ID =-1003254110177

ASK_NAME, ASK_PHONE, ASK_BANK, ASK_LOCATION, ASK_FRONT_ID, ASK_BACK_ID, CONFIRM_ALL = range(7)
SELL_CATEGORY, SELL_DETAILS, SELL_PHOTOS, SELL_CONFIRM = range(100, 104)
EDIT_FIELD_SELECT, EDIT_FIELD_VALUE, ADMIN_EDIT_FIELD_SELECT, ADMIN_EDIT_FIELD_VALUE = range(300, 304)
BUY_CATEGORY, BUY_DETAILS, BUY_PREVIEW, BUY_CONFIRM = range(200, 204)
BUY_EDIT_FIELD_SELECT, BUY_EDIT_FIELD_VALUE = range(204, 206)
ASK_REJECT_REASON, CONFIRM_REJECTION = range(100, 102)
BROADCAST_WAITING, BROADCAST_CONFIRM = range(900, 902)

SELL_DISPLAY_MAPPING = {
    "Smartphones": {
        "Brand & Model:": "Brand & Model",
        "Storage:": "Storage", 
        "RAM:": "RAM",
        "Battery Condition:": "Battery Condition",
        "Condition (New/Used/Refurbished):": "Condition",
        "Price (ETB):": "Price",
        "Other (anything you want to tell for the buyer):": "Other",
        "Contact (Phone/Telegram):": "Contact"
    },
    "Laptops": {
        "Brand & Model:": "Brand & Model",
        "Processor (Intel i5, Ryzen 7, etc.):": "Processor",
        "RAM:": "RAM",
        "Storage (SSD/HDD, size):": "Storage",
        "Graphics (if any):": "Graphics",
        "Battery Condition:": "Battery Condition",
        "Condition (New/Used/Refurbished):": "Condition",
        "Price (ETB):": "Price",
        "Other (anything you want to tell for the buyer):": "Other",
        "Contact (Phone/Telegram):": "Contact"
    },
    "Headsets": {
        "Brand & Model:": "Brand & Model",
        "Type (Wireless/Wired/Noise Cancelling/Gaming):": "Type",
        "Condition (New/Used):": "Condition",
        "Price (ETB):": "Price",
        "Other (anything you want to tell for the buyer):": "Other",
        "Contact (Phone/Telegram):": "Contact"
    },
    "Computers": {
        "Brand & Model / Custom Build:": "Brand & Model",
        "Processor:": "Processor",
        "RAM:": "RAM",
        "Storage:": "Storage",
        "Graphics Card (if any):": "Graphics",
        "Includes Monitor? (Yes/No):": "Includes Monitor",
        "Condition (New/Used):": "Condition",
        "Price (ETB):": "Price",
        "Other (anything you want to tell for the buyer):": "Other",
        "Contact (Phone/Telegram):": "Contact"
    },
    "Power Banks": {
        "Brand & Model:": "Brand & Model",
        "Capacity (mAh):": "Capacity",
        "Condition (New/Used):": "Condition",
        "Price (ETB):": "Price",
        "Other (anything you want to tell for the buyer):": "Other",
        "Contact (Phone/Telegram):": "Contact"
    },
    "Keyboards": {
        "Brand & Model:": "Brand & Model",
        "Type (Mechanical/Wireless/Gaming):": "Type",
        "Condition (New/Used):": "Condition",
        "Price (ETB):": "Price",
        "Other (anything you want to tell for the buyer):": "Other",
        "Contact (Phone/Telegram):": "Contact"
    },
    "Tablets": {
        "Brand & Model:": "Brand & Model",
        "Storage & RAM:": "Storage & RAM",
        "Battery Condition:": "Battery Condition",
        "Condition (New/Used/Refurbished):": "Condition",
        "Price (ETB):": "Price",
        "Other (anything you want to tell for the buyer):": "Other",
        "Contact (Phone/Telegram):": "Contact"
    },
    "Smartwatches": {
        "Brand & Model:": "Brand & Model",
        "Features (GPS, Cellular, Health Tracking):": "Features",
        "Battery Condition:": "Battery Condition",
        "Condition (New/Used):": "Condition",
        "Price (ETB):": "Price",
        "Other (anything you want to tell for the buyer):": "Other",
        "Contact (Phone/Telegram):": "Contact"
    },
    "Monitors": {
        "Brand & Model:": "Brand & Model",
        "Size (inches):": "Size",
        "Resolution (HD/FHD/4K):": "Resolution",
        "Refresh Rate (Hz):": "Refresh Rate",
        "Condition (New/Used):": "Condition",
        "Price (ETB):": "Price",
        "Other (anything you want to tell for the buyer):": "Other",
        "Contact (Phone/Telegram):": "Contact"
    },
    "External Storage": {
        "Brand & Model:": "Brand & Model",
        "Type (HDD/SSD/Flash):": "Type",
        "Capacity:": "Capacity",
        "Condition (New/Used):": "Condition",
        "Price (ETB):": "Price",
        "Other (anything you want to tell for the buyer):": "Other",
        "Contact (Phone/Telegram):": "Contact"
    },
    "Speakers": {
        "Brand & Model:": "Brand & Model",
        "Type (Bluetooth/Wired/Home Theater/Portable):": "Type",
        "Condition (New/Used):": "Condition",
        "Price (ETB):": "Price",
        "Other (anything you want to tell for the buyer):": "Other",
        "Contact (Phone/Telegram):": "Contact"
    },
    "Banks": {
        "Brand & Model:": "Brand & Model",
        "Capacity (mAh):": "Capacity",
        "Condition (New/Used):": "Condition",
        "Price (ETB):": "Price",
        "Other (anything you want to tell for the buyer):": "Other",
        "Contact (Phone/Telegram):": "Contact"
    },
    "Other": {
        "What kind of item you want to sell:": "Item Type",
        "Condition (New/Used):": "Condition",
        "Price (ETB):": "Price",
        "Other (anything you want to tell for the buyer):": "Other",
        "Contact (Phone/Telegram):": "Contact"
    }
}

BUY_DISPLAY_MAPPING = {
    "Smartphones": {
        "Brand & Model (if specific):": "Preferred Brand & Model",
        "Storage preference:": "Storage",
        "RAM preference:": "RAM",
        "Battery Condition preference (if any):": "Battery Condition",
        "Condition (New/Used/Either):": "Condition",
        "Budget (ETB):": "Max Budget",
        "Other (anything you want to tell for the Seller):": "Other",
        "Contact (Phone/Telegram):": "Contact"
    },
    "Laptops": {
        "Brand & Model (if specific):": "Preferred Brand & Model",
        "Processor preference:": "Processor",
        "RAM size:": "RAM",
        "Storage preference (SSD/HDD, size):": "Storage",
        "Graphics preference (if any):": "Graphics",
        "Condition (New/Used/Either):": "Condition",
        "Budget (ETB):": "Max Budget",
        "Other (anything you want to tell for the Seller):": "Other",
        "Contact (Phone/Telegram):": "Contact"
    },
    "Headset": {
        "Brand & Model (if specific):": "Preferred Brand & Model",
        "Type preference (Wireless/Wired/Noise Cancelling/Gaming):": "Type",
        "Condition (New/Used/Either):": "Condition",
        "Budget (ETB):": "Max Budget",
        "Other (anything you want to tell for the Seller):": "Other",
        "Contact (Phone/Telegram):": "Contact"
    },
    "Computer": {
        "Brand/Build preference:": "Brand/Build",
        "Processor:": "Processor",
        "RAM:": "RAM",
        "Storage:": "Storage",
        "Graphics (if needed):": "Graphics",
        "With Monitor? (Yes/No/Either):": "With Monitor",
        "Condition (New/Used/Either):": "Condition",
        "Budget (ETB):": "Max Budget",
        "Other (anything you want to tell for the Seller):": "Other",
        "Contact (Phone/Telegram):": "Contact"
    },
    "Power Bank": {
        "Brand (if specific):": "Brand",
        "Capacity (mAh):": "Capacity",
        "Condition (New/Used/Either):": "Condition",
        "Budget (ETB):": "Max Budget",
        "Other (anything you want to tell for the Seller):": "Other",
        "Contact (Phone/Telegram):": "Contact"
    },
    "Keyboard": {
        "Brand (if specific):": "Brand",
        "Type (Mechanical/Wireless/Gaming):": "Type",
        "Condition (New/Used/Either):": "Condition",
        "Budget (ETB):": "Max Budget",
        "Other (anything you want to tell for the Seller):": "Other",
        "Contact (Phone/Telegram):": "Contact"
    },
    "Tablet": {
        "Brand & Model:": "Preferred Brand & Model",
        "Storage & RAM preference:": "Storage & RAM",
        "Battery condition preference:": "Battery Condition",
        "Condition (New/Used/Either):": "Condition",
        "Budget (ETB):": "Max Budget",
        "Other (anything you want to tell for the Seller):": "Other",
        "Contact (Phone/Telegram):": "Contact"
    },
    "Smartwatche": {
        "Brand & Model:": "Preferred Brand & Model",
        "Features needed (GPS/Cellular/Health Tracking):": "Features Needed",
        "Battery condition preference:": "Battery Condition",
        "Condition (New/Used/Either):": "Condition",
        "Budget (ETB):": "Max Budget",
        "Other (anything you want to tell for the Seller):": "Other",
        "Contact (Phone/Telegram):": "Contact"
    },
    "Monitor": {
        "Brand & Model:": "Preferred Brand & Model",
        "Size preference:": "Size",
        "Resolution preference:": "Resolution",
        "Refresh Rate preference:": "Refresh Rate",
        "Condition (New/Used/Either):": "Condition",
        "Budget (ETB):": "Max Budget",
        "Other (anything you want to tell for the Seller):": "Other",
        "Contact (Phone/Telegram):": "Contact"
    },
    "External Storage": {
        "Brand & Model:": "Preferred Brand & Model",
        "Type (HDD/SSD/Flash):": "Type",
        "Capacity:": "Capacity",
        "Condition (New/Used/Either):": "Condition",
        "Budget (ETB):": "Max Budget",
        "Other (anything you want to tell for the Seller):": "Other",
        "Contact (Phone/Telegram):": "Contact"
    },
    "Speakers": {
        "Brand & Model:": "Preferred Brand & Model",
        "Type (Bluetooth/Wired/Home Theater/Portable):": "Type",
        "Condition (New/Used/Either):": "Condition",
        "Budget (ETB):": "Max Budget",
        "Other (anything you want to tell for the Seller):": "Other",
        "Contact (Phone/Telegram):": "Contact"
    },
    "Other": {
        "What kind of item you want to buy:": "Item Type",
        "Condition (New/Used/Either):": "Condition",
        "Budget (ETB):": "Max Budget",
        "Other (anything you want to tell for the Seller):": "Other",
        "Contact (Phone/Telegram):": "Contact"
    }
}

category_questions = {
    "Smartphones": [
        "Brand & Model:", "Storage:", "RAM:", "Battery Condition:",
        "Condition (New/Used/Refurbished):", "Price (ETB):",
        "Other (anything you want to tell for the buyer):", "Contact (Phone/Telegram):"
    ],
    "Laptops": [
        "Brand & Model:", "Processor (Intel i5, Ryzen 7, etc.):", "RAM:",
        "Storage (SSD/HDD, size):", "Graphics (if any):", "Battery Condition:",
        "Condition (New/Used/Refurbished):", "Price (ETB):",
        "Other (anything you want to tell for the buyer):", "Contact (Phone/Telegram):"
    ],
    "Headsets": [
        "Brand & Model:", "Type (Wireless/Wired/Noise Cancelling/Gaming):",
        "Condition (New/Used):", "Price (ETB):",
        "Other (anything you want to tell for the buyer):", "Contact (Phone/Telegram):"
    ],
    "Computers": [
        "Brand & Model / Custom Build:", "Processor:", "RAM:", "Storage:",
        "Graphics Card (if any):", "Includes Monitor? (Yes/No):",
        "Condition (New/Used):", "Price (ETB):",
        "Other (anything you want to tell for the buyer):", "Contact (Phone/Telegram):"
    ],
    "Power Banks": [
        "Brand & Model:", "Capacity (mAh):", "Condition (New/Used):",
        "Price (ETB):", "Other (anything you want to tell for the buyer):",
        "Contact (Phone/Telegram):"
    ],
    "Keyboards": [
        "Brand & Model:", "Type (Mechanical/Wireless/Gaming):",
        "Condition (New/Used):", "Price (ETB):",
        "Other (anything you want to tell for the buyer):", "Contact (Phone/Telegram):"
    ],
    "Tablets": [
        "Brand & Model:", "Storage & RAM:", "Battery Condition:",
        "Condition (New/Used/Refurbished):", "Price (ETB):",
        "Other (anything you want to tell for the buyer):", "Contact (Phone/Telegram):"
    ],
    "Smartwatches": [
        "Brand & Model:", "Features (GPS, Cellular, Health Tracking):",
        "Battery Condition:", "Condition (New/Used):",
        "Price (ETB):", "Other (anything you want to tell for the buyer):",
        "Contact (Phone/Telegram):"
    ],
    "Monitors": [
        "Brand & Model:", "Size (inches):", "Resolution (HD/FHD/4K):",
        "Refresh Rate (Hz):", "Condition (New/Used):", "Price (ETB):",
        "Other (anything you want to tell for the buyer):", "Contact (Phone/Telegram):"
    ],
    "External Storage": [
        "Brand & Model:", "Type (HDD/SSD/Flash):", "Capacity:",
        "Condition (New/Used):", "Price (ETB):",
        "Other (anything you want to tell for the buyer):", "Contact (Phone/Telegram):"
    ],
    "Speakers": [
        "Brand & Model:", "Type (Bluetooth/Wired/Home Theater/Portable):",
        "Condition (New/Used):", "Price (ETB):",
        "Other (anything you want to tell for the buyer):", "Contact (Phone/Telegram):"
    ],
    "Banks": [
        "Brand & Model:", "Capacity (mAh):", "Condition (New/Used):",
        "Price (ETB):", "Other (anything you want to tell for the buyer):",
        "Contact (Phone/Telegram):"
    ],
    "Other": [
        "What kind of item you want to sell:", "Condition (New/Used):",
        "Price (ETB):", "Other (anything you want to tell for the buyer):",
        "Contact (Phone/Telegram):"
    ]
}

buy_category_questions = {
    "Smartphones": [
        "Brand & Model (if specific):",
        "Storage preference:",
        "RAM preference:",
        "Battery Condition preference (if any):",
        "Condition (New/Used/Either):",
        "Budget (ETB):",
        "Other (anything you want to tell for the Seller):",
        "Contact (Phone/Telegram):"
    ],
    "Laptops": [
        "Brand & Model (if specific):",
        "Processor preference:",
        "RAM size:",
        "Storage preference (SSD/HDD, size):",
        "Graphics preference (if any):",
        "Condition (New/Used/Either):",
        "Budget (ETB):",
        "Other (anything you want to tell for the Seller):",
        "Contact (Phone/Telegram):"
    ],
    "Headset": [
        "Brand & Model (if specific):",
        "Type preference (Wireless/Wired/Noise Cancelling/Gaming):",
        "Condition (New/Used/Either):",
        "Budget (ETB):",
        "Other (anything you want to tell for the Seller):",
        "Contact (Phone/Telegram):"
    ],
    "Computer": [
        "Brand/Build preference:",
        "Processor:",
        "RAM:",
        "Storage:",
        "Graphics (if needed):",
        "With Monitor? (Yes/No/Either):",
        "Condition (New/Used/Either):",
        "Budget (ETB):",
        "Other (anything you want to tell for the Seller):",
        "Contact (Phone/Telegram):"
    ],
    "Power Bank": [
        "Brand (if specific):",
        "Capacity (mAh):",
        "Condition (New/Used/Either):",
        "Budget (ETB):",
        "Other (anything you want to tell for the Seller):",
        "Contact (Phone/Telegram):"
    ],
    "Keyboard": [
        "Brand (if specific):",
        "Type (Mechanical/Wireless/Gaming):",
        "Condition (New/Used/Either):",
        "Budget (ETB):",
        "Other (anything you want to tell for the Seller):",
        "Contact (Phone/Telegram):"
    ],
    "Tablet": [
        "Brand & Model:",
        "Storage & RAM preference:",
        "Battery condition preference:",
        "Condition (New/Used/Either):",
        "Budget (ETB):",
        "Other (anything you want to tell for the Seller):",
        "Contact (Phone/Telegram):"
    ],
    "Smartwatche": [
        "Brand & Model:",
        "Features needed (GPS/Cellular/Health Tracking):",
        "Battery condition preference:",
        "Condition (New/Used/Either):",
        "Budget (ETB):",
        "Other (anything you want to tell for the Seller):",
        "Contact (Phone/Telegram):"
    ],
    "Monitor": [
        "Brand & Model:",
        "Size preference:",
        "Resolution preference:",
        "Refresh Rate preference:",
        "Condition (New/Used/Either):",
        "Budget (ETB):",
        "Other (anything you want to tell for the Seller):",
        "Contact (Phone/Telegram):"
    ],
    "External Storage": [
        "Brand & Model:",
        "Type (HDD/SSD/Flash):",
        "Capacity:",
        "Condition (New/Used/Either):",
        "Budget (ETB):",
        "Other (anything you want to tell for the Seller):",
        "Contact (Phone/Telegram):"
    ],
    "Speakers": [
        "Brand & Model:",
        "Type (Bluetooth/Wired/Home Theater/Portable):",
        "Condition (New/Used/Either):",
        "Budget (ETB):",
        "Other (anything you want to tell for the Seller):",
        "Contact (Phone/Telegram):"
    ],
    "Other": [
        "What kind of item you want to buy:",
        "Condition (New/Used/Either):",
        "Budget (ETB):",
        "Other (anything you want to tell for the Seller):",
        "Contact (Phone/Telegram):"
    ]
}

BUY_CATEGORY_PHOTOS = {
    "Smartphones": "photos/smartphones.jpg",
    "Laptops": "photos/laptops.jpg",
    "Headset": "photos/headsets.jpg",
    "Computer": "photos/computers.jpg",
    "Power Bank": "photos/powerbanks.jpg",
    "Keyboard": "photos/keyboards.jpg",
    "Tablet": "photos/tablets.jpg",
    "Smartwatche": "photos/smartwaches.jpg",
    "Monitor": "photos/monitors.jpg",
    "External Storage": "photos/external_storages.jpg",
    "Speakers": "photos/speakers.jpg",
    "Other": "photos/other.jpg"
}

sell_categories = [
    ["Smartphones", "Banks", "Laptops"],
    ["Keyboards", "Headsets", "Tablets"],
    ["Computers", "Smartwatches", "Power Banks"],
    ["Monitors", "External Storage", "Speakers"],
    ["Other", "⬅️ Back"]
]

buy_categories = [
    ["Smartphones", "Laptops", "Headset"],
    ["Computer", "Power Bank", "Keyboard"],
    ["Tablet", "Smartwatche", "Monitor"],
    ["External Storage", "Speakers", "Other"],
    ["⬅️ Back"]
]