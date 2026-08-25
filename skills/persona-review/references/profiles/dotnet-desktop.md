---
name: dotnet-desktop
display_name: ".NET Desktop (WPF/WinForms)"
build_command: "dotnet build *.sln"
test_command: "dotnet test *.sln"
rotation_size: 5
personas: [implementer, reviewer, tester, ui-ux-designer, security-auditor]
---

# .NET Desktop Review Profile

## Implementer Criteria
- Follow MVVM pattern strictly (WPF) or MVP/MVC (WinForms)
- Use data binding over code-behind event handlers
- Check for proper INotifyPropertyChanged implementations
- Use ObservableCollection for bound lists, not List<T>
- Verify Dispatcher.Invoke/BeginInvoke for cross-thread UI updates
- Ensure async/await is used correctly (no .Result or .Wait() on UI thread)
- `async void` only on an event handler, never on a method you call yourself.
  An exception in an `async void` method cannot be awaited or caught by the
  caller and reaches the runtime as unhandled, which kills the process
- Every `async void` event handler wraps its body in try/catch. There is no
  other place to catch it
- Check that RelayCommand/DelegateCommand CanExecute is wired correctly

## Reviewer Criteria
- Check for disposal of IDisposable resources (streams, DB connections, graphics objects)
- Verify MVVM separation: no business logic in code-behind files
- Look for thread safety issues with UI dispatcher
- Check for proper binding error handling (FallbackValue, TargetNullValue)
- Verify nullable reference type annotations on public APIs
- Look for memory leaks: event handler subscriptions without unsubscription
- Check for proper use of WeakReference where appropriate
- Global unhandled-exception handlers are wired: `DispatcherUnhandledException`
  (WPF) or `Application.ThreadException` (WinForms), plus
  `AppDomain.CurrentDomain.UnhandledException` and
  `TaskScheduler.UnobservedTaskException`. Without them a desktop app dies
  with no log and no message to the user
- Fire-and-forget `Task.Run` whose exception nobody observes is the same
  silent failure in a different shape

## Tester Criteria
- Use MSTest, xUnit, or NUnit per project convention
- Test ViewModels independently from Views
- Mock ICommand implementations for isolated testing
- Test data binding converter edge cases (null, DBNull, unexpected types)
- Test with CultureInfo variations for numeric/date formatting
- Test async commands and their CanExecute state transitions

## UI/UX Designer Criteria
- Review XAML for accessibility (AutomationProperties.Name, AutomationProperties.HelpText)
- Check keyboard navigation (Tab order, focus management, KeyboardNavigation.TabIndex)
- Verify high-DPI scaling behavior (use device-independent units)
- Check theme/style consistency across windows and dialogs
- Review error display patterns (validation adorners, message boxes, status bar)
- Verify window resizing behavior (MinWidth/MinHeight, grid splitters)

## Security Auditor Criteria
- Check for SQL injection in ADO.NET or Entity Framework queries
- Verify file path sanitization for user-supplied paths
- Check for hardcoded connection strings or credentials
- Review serialization/deserialization for untrusted data
- Verify proper use of SecureString for sensitive data in memory
- Check for DLL search order hijacking risks
- Review any P/Invoke declarations for buffer overflow risks

## Project Manager Criteria
- Verify tasks.md is up to date with completed work
- Check Version.props or AssemblyInfo version consistency
- Verify all referenced issues are linked in commit messages
- Confirm installer/packaging configuration is updated if needed
