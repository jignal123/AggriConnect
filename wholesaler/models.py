from django.db import models
from Admin.models import AbstractClassForAll
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
from datetime import date
from farmer.models import CropMaster,Listing


class Wholesaler(AbstractClassForAll):

    class Gender(models.TextChoices):
        MALE = "M",_("MALE")
        FEMALE = "F",_("FEMALE")
    
    class Status(models.TextChoices):
        VERIFIED = "V",_("Verified")
        UNVERIFIED = "U",_("Unverified")

    w_id = models.AutoField(primary_key=True)
    email = models.EmailField(max_length=150,unique=True)
    password = models.CharField(max_length=128)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50, default="")
    gender = models.CharField(max_length=1,choices=Gender.choices)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=50)
    address = models.CharField(max_length=255,default="")
    gst_no = models.CharField(max_length=15,unique=True,validators=[
            RegexValidator(
                regex=r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$',
                message="Enter a valid 15-digit GST number."
            )
        ],
        help_text="Format: 22AAAAA0000A1Z5")
    w_phone = models.CharField(max_length=11,validators=[
            RegexValidator(
                regex=r'^[0-9]{10,11}$',
                message="Enter a valid 10 or 11 digit Phone number."
            )
        ])
    w_photo = models.ImageField(upload_to="wholesaler/",blank=True,null=True)
    aadhar_no = models.CharField(
        max_length=12,
        validators=[
            RegexValidator(
                regex=r"^[2-9]{1}[0-9]{11}$",
                message="Invalid Adhaar card Number. Please Enter Valid Adhaar card Number"
            )
        ],
        unique=True,error_messages={
        "unique": _("Adhaar No Alredy Exist in the site")
    })
    business_proof = models.FileField(upload_to="wholesaler/business_proof/")
    business_name = models.CharField(max_length=150)
    status = models.CharField(max_length=1,choices=Status.choices,default=Status.UNVERIFIED)
    stock = models.ManyToManyField(CropMaster,through="StockMaster")
    biddings = models.ManyToManyField(Listing,through="Bidding") 
    pan_no = models.CharField(
        max_length=10,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$',
                message="Enter a valid 10-digit PAN number (e.g., ABCDE1234F)."
            )
        ]
    )

    @property
    def is_authenticated(self):
        return True


class StockMaster(AbstractClassForAll):
    stock_id = models.AutoField(primary_key=True)
    crop_id = models.ForeignKey(CropMaster,on_delete=models.CASCADE,related_name="wcrops")
    w_id = models.ForeignKey(Wholesaler,on_delete=models.CASCADE)

class StockDetail(AbstractClassForAll):
    class Units(models.TextChoices):
        KG = "kg",_("Kilograms")
        GRAM = "g",_("Grams")
        TON = "TON",_("Metric Tons")
        QUINTAL = "Q",_("Quintal (100kg)") 
    stock_id = models.ForeignKey(StockMaster,on_delete=models.CASCADE,related_name="items")
    intake_date = models.DateField(default=date.today)
    quantity = models.DecimalField(max_digits=8,decimal_places=2)
    unit = models.CharField(max_length=3,choices=Units.choices)
    price_per_unit = models.DecimalField(max_digits=12,decimal_places=2)
    expiry_date = models.DateField(null=True)
    warehouse_loc = models.CharField(max_length=255,blank=True,null=True)

    @property
    def total_price(self):
        return self.quantity * self.price_per_unit

class Bidding(AbstractClassForAll):
    class Status(models.TextChoices):
        PENDING = "P",_("Pending")
        ACCEPTED = "A",_("Accepted")
        REJECTED = "R",_("Rejected")
    b_id = models.AutoField(primary_key=True)
    l_id = models.ForeignKey(Listing,on_delete=models.CASCADE)
    bidder_id = models.ForeignKey(Wholesaler,on_delete=models.CASCADE)
    price_per_unit = models.DecimalField(max_digits=12,decimal_places=2)
    status = models.CharField(max_length=1,choices=Status.choices,default=Status.PENDING)

    class Meta:
        unique_together = ("l_id","bidder_id")

class Orders(AbstractClassForAll):
    class Status(models.TextChoices):
        PENDING_PAYMENT = "Pending",_("Pending Payment")
        PAYMENT_REVIEW = "Review",_("Payment Under Review")
        PAID = "Paid",_("Paid")
        REJECTED = "Rejected",_("Rejected")
    o_id = models.AutoField(primary_key=True)
    b_id = models.ForeignKey(Bidding,on_delete=models.CASCADE)
    order_date = models.DateTimeField(default=date.today)
    status = models.CharField(max_length=9,choices=Status.choices , default= Status.PENDING_PAYMENT)
    price_per_unit = models.DecimalField(max_digits=12,decimal_places=2)
    delivery_date = models.DateTimeField(null=True)