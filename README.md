# inls620-helpdesk-equipment
[INLS 620 Final Project]

## Application Flow Attributes
### Classes
* **search**: Applied to a form, indicates search controls for a collection.
* **equipment**: May appear within a list; indicates a piece of check-out-able equipment.
* **reservation**: May appear within a list; indicates an equipment reservation.
* **edit**: Applied to a form submission control, updates a collection item when submitted
* **edit_equipment**: Applied to a form, indicates the controls to create or update a piece of equipment
* **edit_reservation**: Applied to a form, indicates the controls to create or update a reservation

### Relations
#### IANA Relations
* **collection**: Target is this resource's parent collection (equipment -> equipment collection; reservation -> calendar)
* **item**: Target is an item in this collection (equipment collection -> equipment; calendar -> reservation)
* **related**: Target is a related resource that does not fall under another relation

#### Custom Relations
* **reserve**: Target is a reservation for the current item
* **reservedItem**: Target is the equipment item requested in the current reservation


## Data Types & Properties
### EquipmentItem
Custom subclass of [IndividualProduct](https://schema.org/IndividualProduct). Uses standard properties, with a few custom names:
* **name**: string giving the item's name; inherited from [Thing](https://schema.org/Thing)
* **description**: string describing the item; inherited from [Thing](https://schema.org/Thing)
* **barcode**: string with the item's barcode identifier; my mapping of [IndividualProduct](https://schema.org/IndividualProduct)'s [serialNumber](https://schema.org/serialNumber)
* **replacementCost**: an [Offer](https://schema.org/Offer) containing the [price](https://schema.org/price) to replace the item
* **accessories**: an array listing the accessories available for the item; my mapping of [Product](https://schema.org/Product)'s [isRelatedTo](https://schema.org/isRelatedTo)

### EquipmentReservation
Custom subclass of [Reservation](https://schema.org/Reservation). Uses both standard and custom properties:
* **requestedItem**: the identifier of the equipment reserved; my mapping of [Reservation](https://schema.org/Reservation)'s [reservationFor](https://schema.org/reservationFor)
* **requestedBy**: the email address of the person who made the reservation; my mapping of [Reservation](https://schema.org/Reservation)'s [underName](https://schema.org/underName)
* **modifiedTime**: the datetime when the reservation was last modified; from [Reservation](https://schema.org/Reservation)
* **startDate**: the date the reservation begins; defined for this application
* **endDate**: the date by which the item will be returned; defined for this application
