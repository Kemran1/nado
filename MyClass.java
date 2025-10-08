public class User {
    private String username;
    private String email;
    private int age;
    // Добавляем новое поле
    private String phoneNumber;
    
    // Изменяем конструктор
    public User(String username, String email, int age, String phoneNumber) {
        this.username = username;
        this.email = email;
        this.age = age;
        this.phoneNumber = phoneNumber;
    }
    
    // Добавляем новый метод
    public boolean isValidEmail() {
        return email != null && email.contains("@");
    }
    
    // Добавляем геттер для phoneNumber
    public String getPhoneNumber() {
        return phoneNumber;
    }
    
    public void setPhoneNumber(String phoneNumber) {
        this.phoneNumber = phoneNumber;
    }
}

