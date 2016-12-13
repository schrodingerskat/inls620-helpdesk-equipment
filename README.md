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
