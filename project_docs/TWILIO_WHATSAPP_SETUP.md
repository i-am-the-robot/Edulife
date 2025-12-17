# Twilio WhatsApp Integration - Setup Guide

## 🚀 Quick Setup

### 1. Install Twilio SDK
```bash
pip install twilio
```

### 2. Get Twilio Credentials

**Option A: Twilio Sandbox (Free - For Testing)**
1. Sign up at https://www.twilio.com/try-twilio
2. Go to Console → Messaging → Try it out → Send a WhatsApp message
3. Follow instructions to join sandbox (send "join <code>" to Twilio number)
4. Get credentials:
   - Account SID
   - Auth Token
   - Sandbox WhatsApp Number (usually +1 415 523 8886)

**Option B: Production (Requires Approval)**
1. Apply for WhatsApp Business API access
2. Get approved WhatsApp number
3. Configure templates

### 3. Add to .env File
```env
# Twilio WhatsApp Configuration
TWILIO_ACCOUNT_SID=your_account_sid_here
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886  # Sandbox number
```

### 4. Update requirements.txt
```
twilio>=8.0.0
```

---

## 📱 Parent WhatsApp Number Format

**Nigerian Format:**
```
+234XXXXXXXXXX  (e.g., +2348012345678)
```

**Important:**
- Must include country code (+234 for Nigeria)
- No spaces or dashes
- 10 digits after country code

---

## 🎯 Notification Types

### 1. Quiz Completed
Sent when student finishes a quiz
```
🎓 EduLife Update
Hello! Your child Ada just completed a Mathematics quiz.
📊 Score: 8/10 (80%)
🌟 Great job!
```

### 2. Achievement Unlocked
Sent when student earns achievement
```
🏆 EduLife Achievement
Congratulations! Ada has earned an achievement:
Mastered Algebra
Keep up the amazing work! 🌟
```

### 3. Inactivity Alert
Sent when student is inactive
```
📚 EduLife Reminder
Hello! We noticed that Ada hasn't been active on EduLife for 5 days.
Regular learning helps maintain progress. Please encourage them to log in!
```

### 4. Study Plan Created
Sent when AI creates study plan
```
📅 EduLife Study Plan
Good news! A personalized study plan has been created for Ada.
Goal: Prepare for Math exam
Deadline: 2025-12-20
```

### 5. Weekly Summary
Sent every Sunday
```
📊 EduLife Weekly Summary
Here's how Ada performed this week:
✅ Quizzes Completed: 12
📈 Average Score: 85%
📅 Active Days: 6/7
🏆 Achievements: 3
🌟 Excellent progress!
```

### 6. Exam Reminder
Sent 3 days before exam
```
⏰ EduLife Exam Reminder
Ada has an exam coming up!
📚 Subject: Mathematics
📅 In 3 days
Our AI agents have created a preparation plan.
```

---

## 🔧 Integration with Agents

### Assessment Agent → Quiz Completed
```python
from .twilio_whatsapp_service import notify_parent

# After quiz completion
if student.parent_whatsapp:
    notify_parent(
        student.parent_whatsapp,
        "quiz_completed",
        student_name=student.full_name,
        subject=subject,
        score=correct_answers,
        total=total_questions
    )
```

### Motivation Agent → Achievement
```python
# After milestone
if student.parent_whatsapp:
    notify_parent(
        student.parent_whatsapp,
        "achievement",
        student_name=student.full_name,
        achievement="Mastered Algebra",
        description="Completed all algebra topics with 90%+ scores!"
    )
```

### Coordinator → Study Plan
```python
# After creating exam prep plan
if student.parent_whatsapp:
    notify_parent(
        student.parent_whatsapp,
        "study_plan",
        student_name=student.full_name,
        plan_goal=plan.goal,
        deadline=plan.deadline.strftime("%Y-%m-%d")
    )
```

### Proactive Check-in → Inactivity
```python
# When student is inactive
if student.parent_whatsapp:
    notify_parent(
        student.parent_whatsapp,
        "inactivity",
        student_name=student.full_name,
        days_inactive=days_inactive
    )
```

---

## 🧪 Testing

### Test WhatsApp Message
```python
from backend.twilio_whatsapp_service import whatsapp_service

# Send test message
whatsapp_service.send_whatsapp_message(
    to_number="+2348012345678",
    message="Hello from EduLife! This is a test message."
)
```

### Test Notification
```python
from backend.twilio_whatsapp_service import notify_parent

notify_parent(
    parent_whatsapp="+2348012345678",
    notification_type="achievement",
    student_name="Ada",
    achievement="First Quiz Completed",
    description="Completed first Mathematics quiz with 80% score!"
)
```

---

## 📋 Frontend Integration

### Add Parent WhatsApp to Registration Form

**File:** `frontend/src/pages/admin/Students.jsx`

Add field to form:
```javascript
<div>
  <label className="block text-sm font-medium text-gray-700 mb-2">
    Parent WhatsApp Number
  </label>
  <input
    type="tel"
    name="parent_whatsapp"
    value={formData.parent_whatsapp || ''}
    onChange={handleInputChange}
    placeholder="+2348012345678"
    className="w-full px-4 py-2 border border-gray-300 rounded-lg"
  />
  <p className="text-xs text-gray-500 mt-1">
    Format: +234XXXXXXXXXX (for WhatsApp notifications)
  </p>
</div>
```

Add to formData state:
```javascript
const [formData, setFormData] = useState({
  // ... existing fields
  parent_whatsapp: ''
});
```

---

## 🔒 Privacy & Compliance

**Important Considerations:**
1. **Consent:** Get parent consent for WhatsApp notifications
2. **Opt-out:** Provide way to disable notifications
3. **Data Protection:** Store phone numbers securely
4. **Rate Limiting:** Don't spam parents with too many messages
5. **Twilio Costs:** Monitor usage (sandbox is free, production has costs)

---

## 💰 Costs (Production)

**Twilio WhatsApp Pricing (Nigeria):**
- Business-initiated: ~$0.005 per message
- User-initiated: Free (first 24 hours)
- Monthly: Depends on volume

**Recommendation:**
- Start with Sandbox (free)
- Monitor engagement
- Upgrade to production when ready

---

## 🎯 Best Practices

1. **Timing:** Send notifications at appropriate times (not late night)
2. **Frequency:** Limit to important updates (max 2-3 per day)
3. **Language:** Use clear, friendly language
4. **Emojis:** Use sparingly for visual appeal
5. **Actionable:** Include clear next steps
6. **Branding:** Consistent "EduLife" signature

---

## 🚨 Troubleshooting

**Message not sending?**
- Check Twilio credentials in .env
- Verify phone number format (+234...)
- Check Twilio console for errors
- Ensure parent joined sandbox (for testing)

**Parent not receiving?**
- Verify they joined Twilio sandbox
- Check phone number is correct
- Check WhatsApp is installed
- Try sending test message from Twilio console

---

## ✅ Summary

**What's Implemented:**
✅ Twilio WhatsApp service
✅ 6 notification types
✅ Parent WhatsApp field in Student model
✅ Integration helpers
✅ Error handling

**Next Steps:**
1. Add Twilio credentials to .env
2. Install twilio package
3. Add parent_whatsapp to registration form
4. Test with Twilio sandbox
5. Integrate with agents

**Demo Ready!** 🚀
