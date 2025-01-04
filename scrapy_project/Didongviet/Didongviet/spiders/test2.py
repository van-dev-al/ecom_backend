from seleniumbase import BaseCase

class WebsiteLoginTest(BaseCase):
    def test_login_and_get_data(self):
        # Open the login page
        self.open("https://dropbuy.vn/dang-nhap?callbackUrl=https%3A%2F%2Fdropbuy.vn%2F")  # Replace with your website's login URL

        # Enter username and password
        self.type("#username", "matrix")  # Replace #username with the actual username field selector
        self.type("#password", "tlu@2020")  # Replace #password with the actual password field selector
        
        # Click the login button
        self.click("body > div > main > div > div > div > div > div:nth-child(2) > form > div:nth-child(2) > div > div > div > div > div > button")  # Replace #loginButton with the actual login button selector
        
        # Wait for the next page to load (optional)
        self.wait_for_element("body > div.css-1p4n0f9.ant-app.flex.flex-col.min-h-screen.bg-gray-100.css-var-Rsva > main > div > div:nth-child(3) > div.grid.grid-cols-2.gap-4.md\:grid-cols-3.lg\:grid-cols-6")  # Replace with a unique element on the page after login
        
        # Navigate to the target page or section
        self.open("https://bff.pen.dropbuy.vn/bff/variations/get-price")  # Replace with the URL you want to scrape
        
        # Extract data
        data = self.get_text("body > div.css-1p4n0f9.ant-app.flex.flex-col.min-h-screen.bg-gray-100.css-var-Rsva > main > div > div:nth-child(3) > div.grid.grid-cols-2.gap-4.md\:grid-cols-3.lg\:grid-cols-6 > a:nth-child(1) > div > div.px-3.py-1.mt-2 > div.flex.items-center.justify-between > div > div.font-semibold.text-red-500")  # Replace div.target-data with the selector of the data element
        
        # Print or process the extracted data
        print("Extracted Data:", data)
