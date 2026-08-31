# Issue Context Dossier: `openstreetmap/openstreetmap-website` #7285

**Title:** Let the user delete notifications  
**Repository:** https://github.com/openstreetmap/openstreetmap-website  
**Language:** Ruby  
**Suitability Score:** 92/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> The notifications page currently lists every notification a user has ever received without providing a way to delete individual notifications or clear them in bulk. This issue requests adding the ability for users to delete individual or bulk notifications, similar to the existing private message inbox functionality.

## 2. Root Cause Analysis
> The notifications feature was introduced in #7030 to list all historical notifications, but a deletion mechanism (similar to Message destruction in MessagesController#destroy) was not implemented.

## 3. Grounded Code Locations & Citations
- File: `app/controllers/notifications_controller.rb` (Lines: `1-29`) | Symbol: `NotificationsController` | Role: *Controller displaying the user notifications list* (Verified: True)
- File: `app/controllers/messages_controller.rb` (Lines: `36-75`) | Symbol: `MessagesController#destroy` | Role: *Reference implementation for resource destruction and user authorization check* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect NotificationsController Control Flow**: Inspect NotificationsController in app/controllers/notifications_controller.rb and compare it against MessagesController in app/controllers/messages_controller.rb to understand authorization patterns and destroy action handling. (Target: `app/controllers/notifications_controller.rb`)
2. **Implement destroy Action in NotificationsController**: Add the destroy action to NotificationsController in app/controllers/notifications_controller.rb to find the notification belonging to current_user, destroy it, and redirect back to the notifications index with a success flash message. (Target: `app/controllers/notifications_controller.rb`)
3. **Update Routes and Notifications View**: Add resource or member route for destruction under notifications in config/routes.rb and add delete buttons/forms for each notification item in app/views/notifications/index.html.erb. (Target: `config/routes.rb`)
4. **Add Regression Test and Run Test Suite**: Add controller or system tests verifying that a user can successfully delete their notification and that unauthorized users cannot delete other users' notifications, then execute the test suite. (Target: `test/controllers/notifications_controller_test.rb`)

## 5. Educational Concepts
### Resource Destruction in Ruby on Rails
- **What is it:** The pattern of finding a database record belonging to the current user and calling destroy or updating visibility flags.
- **Why it matters:** Ensures users can only delete or modify their own data securely without affecting other users.
- **Connection to Issue:** Implementing notification deletion requires adding a destroy action that locates the notification belonging to the current_user and removes it or marks it deleted.

### Controller Action Authorization and Database Writable Checks
- **What is it:** Filters like before_action :check_database_writable and authorization checks to guard write operations.
- **Why it matters:** Prevents unauthorized modifications and protects read-only database replicas from receiving write queries.
- **Connection to Issue:** Any new delete or destroy action added to NotificationsController must ensure database writability and proper authorization.

