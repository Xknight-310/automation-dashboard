from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from .models import Task
from .forms import TaskForm
from .services.stats import task_completion_stats, weekly_productivity


class TaskModelTestCase(TestCase):
    """Tests for the Task model"""
    
    def setUp(self):
        """Set up test user and tasks"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.today = timezone.now().date()
    
    def test_task_creation(self):
        """Test creating a task with required fields"""
        task = Task.objects.create(
            user=self.user,
            title='Test Task',
            description='Test Description'
        )
        self.assertEqual(task.title, 'Test Task')
        self.assertEqual(task.user, self.user)
        self.assertEqual(task.status, 'todo')
        self.assertEqual(task.priority, 'medium')
    
    def test_task_str_representation(self):
        """Test the string representation of Task"""
        task = Task.objects.create(
            user=self.user,
            title='My Task'
        )
        self.assertEqual(str(task), 'My Task')
    
    def test_task_status_choices(self):
        """Test all status choices"""
        statuses = ['todo', 'doing', 'done']
        for status in statuses:
            task = Task.objects.create(
                user=self.user,
                title=f'Task {status}',
                status=status
            )
            self.assertEqual(task.status, status)
    
    def test_task_priority_choices(self):
        """Test all priority choices"""
        priorities = ['low', 'medium', 'high']
        for priority in priorities:
            task = Task.objects.create(
                user=self.user,
                title=f'Task {priority}',
                priority=priority
            )
            self.assertEqual(task.priority, priority)
    
    def test_task_is_overdue_true(self):
        """Test is_overdue returns True for past due date"""
        task = Task.objects.create(
            user=self.user,
            title='Overdue Task',
            due_date=self.today - timedelta(days=1),
            status='todo'
        )
        self.assertTrue(task.is_overdue())
    
    def test_task_is_overdue_false_future_date(self):
        """Test is_overdue returns False for future due date"""
        task = Task.objects.create(
            user=self.user,
            title='Future Task',
            due_date=self.today + timedelta(days=1),
            status='todo'
        )
        self.assertFalse(task.is_overdue())
    
    def test_task_is_overdue_false_completed(self):
        """Test is_overdue returns False for completed tasks"""
        task = Task.objects.create(
            user=self.user,
            title='Completed Overdue',
            due_date=self.today - timedelta(days=1),
            status='done'
        )
        self.assertFalse(task.is_overdue())
    
    def test_task_is_overdue_no_due_date(self):
        """Test is_overdue returns False when no due date"""
        task = Task.objects.create(
            user=self.user,
            title='No Due Date',
            status='todo'
        )
        self.assertFalse(task.is_overdue())
    
    def test_task_is_complete_true(self):
        """Test is_complete returns True for done status"""
        task = Task.objects.create(
            user=self.user,
            title='Completed Task',
            status='done'
        )
        self.assertTrue(task.is_complete())
    
    def test_task_is_complete_false(self):
        """Test is_complete returns False for non-done status"""
        for status in ['todo', 'doing']:
            task = Task.objects.create(
                user=self.user,
                title=f'Not Complete {status}',
                status=status
            )
            self.assertFalse(task.is_complete())
    
    def test_task_completed_at_field(self):
        """Test completed_at field can be set"""
        now = timezone.now()
        task = Task.objects.create(
            user=self.user,
            title='Task with completion time',
            completed_at=now
        )
        self.assertEqual(task.completed_at, now)
    
    def test_task_user_cascade_delete(self):
        """Test that tasks are deleted when user is deleted"""
        task = Task.objects.create(
            user=self.user,
            title='Task to delete'
        )
        self.assertEqual(Task.objects.count(), 1)
        self.user.delete()
        self.assertEqual(Task.objects.count(), 0)


class TaskFormTestCase(TestCase):
    """Tests for the TaskForm"""
    
    def test_form_valid_data(self):
        """Test form with valid data"""
        form_data = {
            'title': 'Test Task',
            'description': 'Test Description',
            'due_date': '2026-02-15',
            'status': 'todo',
            'priority': 'high'
        }
        form = TaskForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_form_missing_title(self):
        """Test form without title"""
        form_data = {
            'description': 'Test Description',
            'status': 'todo',
            'priority': 'high'
        }
        form = TaskForm(data=form_data)
        self.assertFalse(form.is_valid())
    
    def test_form_optional_fields(self):
        """Test form with only required title field"""
        form_data = {
            'title': 'Minimal Task',
            'due_date': '2026-02-15',
            'status': 'todo',
            'priority': 'medium'
        }
        form = TaskForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_form_fields(self):
        """Test that form contains correct fields"""
        form = TaskForm()
        expected_fields = ['title', 'description', 'due_date', 'status', 'priority']
        self.assertEqual(list(form.fields.keys()), expected_fields)
    
    def test_form_blank_description(self):
        """Test form allows blank description"""
        form_data = {
            'title': 'Task Without Description',
            'description': '',
            'due_date': '2026-05-22',
            'status': 'todo',
            'priority': 'high'
        }
        form = TaskForm(data=form_data)
        # print('\033[31;1;4m', "ERROR ", form.data ,'\033[0m')
        self.assertTrue(form.is_valid())
    
    def test_form_instance_update(self):
        """Test form with instance for updating"""
        user = User.objects.create_user(
            username='testuser',
            password='testpass'
        )
        task = Task.objects.create(
            user=user,
            title='Original Title',
            due_date="2026-05-22",
            status= 'doing',
            priority='low'
        )
        form_data = {
            'title': 'Updated Title',
            'due_date': '2026-05-22',
            'status': 'done',
            'priority': 'high'
        }
        form = TaskForm(data=form_data, instance=task)
        self.assertTrue(form.is_valid())


class TaskViewsTestCase(TestCase):
    """Tests for Task views"""
    
    def setUp(self):
        """Set up test client and user"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.today = timezone.now().date()
    
    def test_home_view_anonymous(self):
        """Test home view is accessible without login"""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/home.html')
    
    def test_task_list_requires_login(self):
        """Test task_list view requires login"""
        response = self.client.get(reverse('task_list'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_task_list_authenticated(self):
        """Test task_list view with authenticated user"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('task_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/task_list.html')
    
    def test_task_list_filter_today(self):
        """Test task_list with today filter"""
        Task.objects.create(
            user=self.user,
            title='Today Task',
            due_date=self.today
        )
        Task.objects.create(
            user=self.user,
            title='Tomorrow Task',
            due_date=self.today + timedelta(days=1)
        )
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('task_list'), {'filter': 'today'})
        self.assertEqual(len(response.context['tasks']), 1)
        self.assertEqual(response.context['tasks'][0].title, 'Today Task')
    
    def test_task_list_filter_week(self):
        """Test task_list with week filter"""
        Task.objects.create(
            user=self.user,
            title='Week Task',
            due_date=self.today + timedelta(days=3)
        )
        Task.objects.create(
            user=self.user,
            title='Next Month Task',
            due_date=self.today + timedelta(days=40)
        )
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('task_list'), {'filter': 'week'})
        self.assertEqual(len(response.context['tasks']), 1)
    
    def test_task_list_filter_done(self):
        """Test task_list with done filter"""
        Task.objects.create(
            user=self.user,
            title='Done Task',
            status='done'
        )
        Task.objects.create(
            user=self.user,
            title='Todo Task',
            status='todo'
        )
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('task_list'), {'filter': 'done'})
        self.assertEqual(len(response.context['tasks']), 1)
        self.assertEqual(response.context['tasks'][0].status, 'done')
    
    def test_task_create_get(self):
        """Test task_create GET request"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('task_create'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/task_form.html')
        self.assertIsInstance(response.context['form'], TaskForm)
    
    def test_task_create_post_valid(self):
        """Test task_create with valid POST data"""
        self.client.login(username='testuser', password='testpass123')
        form_data = {
            'title': 'New Task',
            'description': 'New Description',
            'status': 'todo',
            'priority': 'high'
        }
        response = self.client.post(reverse('task_create'), form_data)
        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.assertEqual(Task.objects.count(), 1)
        task = Task.objects.first()
        self.assertEqual(task.title, 'New Task')
        self.assertEqual(task.user, self.user)
    
    def test_task_create_sets_completed_at(self):
        """Test that creating a done task sets completed_at"""
        self.client.login(username='testuser', password='testpass123')
        form_data = {
            'title': 'Completed Task',
            'status': 'done',
            'priority': 'medium'
        }
        response = self.client.post(reverse('task_create'), form_data)
        self.assertEqual(response.status_code, 302)
        task = Task.objects.first()
        self.assertIsNotNone(task)
        self.assertIsNotNone(task.completed_at)
    
    def test_task_update_get(self):
        """Test task_update GET request"""
        task = Task.objects.create(
            user=self.user,
            title='Task to Update'
        )
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('task_update', kwargs={'pk': task.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/task_form.html')
    
    def test_task_update_post_valid(self):
        """Test task_update with valid POST data"""
        task = Task.objects.create(
            user=self.user,
            title='Original Title',
            priority='low'
        )
        self.client.login(username='testuser', password='testpass123')
        form_data = {
            'title': 'Updated Title',
            'priority': 'high',
            'status': 'doing'
        }
        response = self.client.post(
            reverse('task_update', kwargs={'pk': task.pk}),
            form_data
        )
        self.assertEqual(response.status_code, 302)
        task.refresh_from_db()
        self.assertEqual(task.title, 'Updated Title')
        self.assertEqual(task.priority, 'high')
    
    def test_task_update_wrong_user(self):
        """Test that users can't update other users' tasks"""
        other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )
        task = Task.objects.create(
            user=other_user,
            title='Other User Task'
        )
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('task_update', kwargs={'pk': task.pk}))
        self.assertEqual(response.status_code, 404)
    
    def test_task_delete_get(self):
        """Test task_delete GET request"""
        task = Task.objects.create(
            user=self.user,
            title='Task to Delete'
        )
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('task_delete', kwargs={'pk': task.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/task_confirm_delete.html')
    
    def test_task_delete_post(self):
        """Test task_delete with POST request"""
        task = Task.objects.create(
            user=self.user,
            title='Task to Delete'
        )
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(reverse('task_delete', kwargs={'pk': task.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Task.objects.count(), 0)
    
    def test_task_delete_wrong_user(self):
        """Test that users can't delete other users' tasks"""
        other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )
        task = Task.objects.create(
            user=other_user,
            title='Other User Task'
        )
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('task_delete', kwargs={'pk': task.pk}))
        self.assertEqual(response.status_code, 404)
    
    def test_stats_view_requires_login(self):
        """Test stats_view requires login"""
        response = self.client.get(reverse('stats'))
        self.assertEqual(response.status_code, 302)
    
    def test_stats_view_authenticated(self):
        """Test stats_view with authenticated user"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('stats'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/stats.html')
        self.assertIn('stats', response.context)
        self.assertIn('weekly_data', response.context)
    
    def test_user_logout(self):
        """Test that user can logout and loses access to protected views"""
        self.client.login(username='testuser', password='testpass123')
        # Verify user is logged in by accessing protected view
        response = self.client.get(reverse('task_list'))
        self.assertEqual(response.status_code, 200)
        
        # Logout
        self.client.logout()
        
        # Verify user cannot access protected view after logout
        response = self.client.get(reverse('task_list'))
        self.assertEqual(response.status_code, 302)  # Redirect to login


class TaskStatsTestCase(TestCase):
    """Tests for task statistics functions"""
    
    def setUp(self):
        """Set up test user and tasks"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.today = timezone.now().date()
    
    def test_task_completion_stats_empty(self):
        """Test stats with no tasks"""
        stats = task_completion_stats(self.user)
        self.assertEqual(stats['total'], 0)
        self.assertEqual(stats['completed'], 0)
        self.assertEqual(stats['open'], 0)
        self.assertEqual(stats['completion_rate'], 0)
    
    def test_task_completion_stats_all_completed(self):
        """Test stats with all tasks completed"""
        Task.objects.create(user=self.user, title='Task 1', status='done')
        Task.objects.create(user=self.user, title='Task 2', status='done')
        stats = task_completion_stats(self.user)
        self.assertEqual(stats['total'], 2)
        self.assertEqual(stats['completed'], 2)
        self.assertEqual(stats['open'], 0)
        self.assertEqual(stats['completion_rate'], 100.0)
    
    def test_task_completion_stats_partial(self):
        """Test stats with partial completion"""
        Task.objects.create(user=self.user, title='Task 1', status='done')
        Task.objects.create(user=self.user, title='Task 2', status='todo')
        stats = task_completion_stats(self.user)
        self.assertEqual(stats['total'], 2)
        self.assertEqual(stats['completed'], 1)
        self.assertEqual(stats['open'], 1)
        self.assertEqual(stats['completion_rate'], 50.0)
    
    def test_task_completion_stats_by_status(self):
        """Test stats breakdown by status"""
        Task.objects.create(user=self.user, title='Task 1', status='todo')
        Task.objects.create(user=self.user, title='Task 2', status='doing')
        Task.objects.create(user=self.user, title='Task 3', status='done')
        stats = task_completion_stats(self.user)
        by_status = {item['status']: item['count'] for item in stats['by_status']}
        self.assertEqual(by_status['todo'], 1)
        self.assertEqual(by_status['doing'], 1)
        self.assertEqual(by_status['done'], 1)
    
    def test_task_completion_stats_by_priority(self):
        """Test stats breakdown by priority"""
        Task.objects.create(user=self.user, title='Task 1', priority='low')
        Task.objects.create(user=self.user, title='Task 2', priority='medium')
        Task.objects.create(user=self.user, title='Task 3', priority='high')
        stats = task_completion_stats(self.user)
        by_priority = {item['priority']: item['count'] for item in stats['by_priority']}
        self.assertEqual(by_priority['low'], 1)
        self.assertEqual(by_priority['medium'], 1)
        self.assertEqual(by_priority['high'], 1)
    
    def test_weekly_productivity_empty(self):
        """Test weekly productivity with no completed tasks"""
        data = weekly_productivity(self.user)
        self.assertIn('result', data)
        self.assertIn('fake', data)
    
    def test_weekly_productivity_with_tasks(self):
        """Test weekly productivity with completed tasks"""
        now = timezone.now()
        Task.objects.create(
            user=self.user,
            title='Completed Today',
            status='done',
            completed_at=now
        )
        data = weekly_productivity(self.user)
        self.assertEqual(len(data['result']), 1)
        self.assertEqual(data['result'][0]['count'], 1)
        self.assertFalse(data['fake'])
    
    def test_weekly_productivity_multiple_days(self):
        """Test weekly productivity across multiple days"""
        now = timezone.now()
        for i in range(3):
            Task.objects.create(
                user=self.user,
                title=f'Task {i}',
                status='done',
                completed_at=now - timedelta(days=i)
            )
        data = weekly_productivity(self.user)
        self.assertEqual(len(data['result']), 3)
        self.assertFalse(data['fake'])
