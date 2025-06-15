#!/usr/bin/env python3



import pygame
import os
import openai # type: ignore
import time
import threading  # NEW: import threading for background sorting

# Initialize Pygame
pygame.init()

# Set up the screen dimensions and create display
WIDTH = 800
HEIGHT = 500
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Bubble Sort Visualization with AI Insights")

# Define Colors and Font
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED   = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE  = (0, 0, 255)
FONT  = pygame.font.SysFont(None, 20)

# OpenAI API Key (replace with your API key)
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Sample array and bar layout settings
array = [30, 70, 20, 90, 50]
BAR_WIDTH = 40
BAR_GAP   = 10

# Layout settings:
TEXT_BOX_HEIGHT   = 100  # Reserved for AI insights text at the top (left side)
TOP_MARGIN_BARS   = 10
BOTTOM_MARGIN     = 30   # Reserved for drawing bar values below bars
BAR_AREA_TOP      = TEXT_BOX_HEIGHT + TOP_MARGIN_BARS
BAR_AREA_HEIGHT   = HEIGHT - BAR_AREA_TOP - BOTTOM_MARGIN

# Control Panel Settings (right side)
CONTROL_PANEL_WIDTH = 120
BAR_AREA_WIDTH = WIDTH - CONTROL_PANEL_WIDTH  # Only draw bars in left region

# Global state for pause/resume and text input
paused = False
question_text = ""
gpt_response = ""

# Define Control Panel UI Rectangles
pause_button_rect   = pygame.Rect(WIDTH - CONTROL_PANEL_WIDTH + 10, 20, 100, 40)
question_box_rect   = pygame.Rect(WIDTH - CONTROL_PANEL_WIDTH + 10, 80, 100, 40)
send_button_rect    = pygame.Rect(WIDTH - CONTROL_PANEL_WIDTH + 10, 130, 40, 40)
response_box_rect   = pygame.Rect(WIDTH - CONTROL_PANEL_WIDTH + 10, 180, 100, 80)

def handle_pause():
    global paused
    while paused:
        pygame.event.pump()  # Ensure events are processed
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
        time.sleep(0.01)

def custom_sleep(seconds):
    start = time.time()
    while time.time() - start < seconds:
        pygame.event.pump()  # Process event queue more frequently
        handle_pause()       # Wait here if paused
        time.sleep(0.01)

def draw_bars(array, color_positions=None):
    """
    Draws the sorting bars (and value texts underneath each bar) in the left area.
    Clears the bar area plus the bottom margin reserved for the value texts.
    """
    combined_rect = pygame.Rect(0, BAR_AREA_TOP, BAR_AREA_WIDTH, BAR_AREA_HEIGHT + BOTTOM_MARGIN)
    pygame.draw.rect(SCREEN, BLACK, combined_rect)
    
    max_value = max(array)
    color_positions = color_positions or {}
    
    for i, value in enumerate(array):
        # Calculate bar dimensions
        bar_height = (value / max_value) * BAR_AREA_HEIGHT
        x_pos = i * (BAR_WIDTH + BAR_GAP) + 50
        y_pos = (BAR_AREA_TOP + BAR_AREA_HEIGHT) - bar_height
        color = color_positions.get(i, BLUE)
        pygame.draw.rect(SCREEN, color, (x_pos, y_pos, BAR_WIDTH, bar_height))
        
        # Draw the value text underneath the bar, centered in the bottom margin
        value_text = FONT.render(str(value), True, WHITE)
        text_rect = value_text.get_rect()
        x_text = x_pos + (BAR_WIDTH - text_rect.width) // 2
        y_text = BAR_AREA_TOP + BAR_AREA_HEIGHT + (BOTTOM_MARGIN - text_rect.height) // 2
        SCREEN.blit(value_text, (x_text, y_text))
    
    pygame.display.update(combined_rect)

def display_insight(text):
    """
    Displays the AI insight text in the designated text box (top left area).
    Performs simple word-wrapping and draws a border around the insight box.
    """
    insight_rect = pygame.Rect(0, 0, BAR_AREA_WIDTH, TEXT_BOX_HEIGHT)
    pygame.draw.rect(SCREEN, BLACK, insight_rect)
    
    words = text.split(' ')
    lines = []
    current_line = ''
    for word in words:
        if FONT.size(current_line + word)[0] < BAR_AREA_WIDTH - 20:
            current_line += word + ' '
        else:
            lines.append(current_line)
            current_line = word + ' '
    lines.append(current_line)
    
    y_pos = 10
    for line in lines:
        rendered_line = FONT.render(line, True, WHITE)
        SCREEN.blit(rendered_line, (10, y_pos))
        y_pos += FONT.get_height() + 5
        
    pygame.draw.rect(SCREEN, WHITE, insight_rect, 2)
    pygame.display.update(insight_rect)

def draw_control_panel():
    """
    Draws the control panel on the right side of the screen.
    When paused, it draws the pause/resume button, the question textbox, send button, and response box.
    """
    panel_rect = pygame.Rect(WIDTH - CONTROL_PANEL_WIDTH, 0, CONTROL_PANEL_WIDTH, HEIGHT)
    pygame.draw.rect(SCREEN, (30, 30, 30), panel_rect)  # Dark gray background for the panel

    # Draw Pause/Resume Button
    button_text = "Resume" if paused else "Pause"
    pygame.draw.rect(SCREEN, BLUE, pause_button_rect)
    btn_text_render = FONT.render(button_text, True, WHITE)
    btn_text_rect = btn_text_render.get_rect(center=pause_button_rect.center)
    SCREEN.blit(btn_text_render, btn_text_rect)

    # When paused, show the question input area and response textbox
    # if paused:
        # # Draw the Question Textbox
        # pygame.draw.rect(SCREEN, WHITE, question_box_rect, 2)
        # question_render = FONT.render(question_text, True, WHITE)
        # SCREEN.blit(question_render, (question_box_rect.x + 5, question_box_rect.y + 10))
        
        # # Draw the Send Button (arrow)
        # pygame.draw.rect(SCREEN, BLUE, send_button_rect)
        # send_text = FONT.render("→", True, WHITE)
        # send_text_rect = send_text.get_rect(center=send_button_rect.center)
        # SCREEN.blit(send_text, send_text_rect)
        
        # # Draw the Response Box for GPT answer
        # pygame.draw.rect(SCREEN, WHITE, response_box_rect, 2)
        # response_render = FONT.render(gpt_response, True, WHITE)
        # SCREEN.blit(response_render, (response_box_rect.x + 5, response_box_rect.y + 10))
    
    # pygame.display.update(panel_rect)

def ask_question(question):
    """
    Sends the user's question to GPT-4o via the OpenAI API and returns the answer.
    """
    prompt = f"User question: {question}\nPlease provide an educational explanation or answer."
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an AI tutor answering user queries about sorting algorithms."},
                {"role": "user", "content": prompt}
            ]
        )
        answer = response.choices[0].message.content
        return answer
    except Exception as e:
        return f"Error: {e}"

def generate_insight(array, index1, index2, swapped):
    """
    Generates an AI insight using the OpenAI API for the current comparison/swap.
    """
    state_description = f"The current array is {array}. Comparing {array[index1]} and {array[index2]}."
    action_description = f"Swapped {array[index1]} and {array[index2]}." if swapped else "No swap performed."
    prompt = f"{state_description} {action_description} Explain why this decision makes sense based on sorting logic in 30 or less words."
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an AI tutor explaining bubble sorting algorithm steps."},
                {"role": "user", "content": prompt}
            ]
        )
        insight = response.choices[0].message.content
        return insight
    except Exception as e:
        return f"Error generating AI insight: {e}"

def bubble_sort_with_insights(array):
    """
    Performs the Bubble Sort while updating the Pygame window with bar animations and AI insights.
    Uses custom_sleep() in place of time.sleep() for delays, enabling pause/resume support at any time.
    """
    n = len(array)
    for i in range(n):
        for j in range(n - i - 1):
            # snapshot before change
            pre = array.copy()
            swapped = False
            # Show comparison: color the two bars being compared in red.
            draw_bars(array, {j: RED, j+1: RED})
            display_insight(f"Comparing {array[j]} and {array[j+1]}")
            custom_sleep(3)
            if array[j] > array[j+1]:
                # Show swap initiation: color the two bars in green.
                draw_bars(array, {j: GREEN, j+1: GREEN})
                display_insight(f"Swapping {array[j]} and {array[j+1]}")
                custom_sleep(1)
                array[j], array[j+1] = array[j+1], array[j]
                swapped = True
            else:
                display_insight(f"No swap needed for {array[j]} and {array[j+1]}")
                custom_sleep(1)
            
            # For testing pause/resume responsiveness, the GPT insight calls are commented out:
            insight = generate_insight(pre, j, j+1, swapped)
            display_insight("GPT insight: " + insight)
            custom_sleep(2)
            
            # Refresh the bar area after the update.
            draw_bars(array, {j: RED, j+1: RED})
            custom_sleep(1)
        
        # Optionally mark the sorted portion with a different color.
        draw_bars(array, {k: WHITE for k in range(n - i, n)})
        display_insight("Sorted portion marked.")
        custom_sleep(1)
    
    # Final drawing update after sorting is complete.
    draw_bars(array)
    display_insight("Sorting Complete!")
    custom_sleep(1)

def main():
    global paused, question_text, gpt_response
    clock = pygame.time.Clock()
    running = True
    sort_thread = None  # NEW: to track the sorting thread

    # Initial drawing of bars and instructions
    draw_bars(array)
    display_insight("Press SPACE to start Bubble Sort with AI insights.")
    draw_control_panel()

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # Check for mouse clicks in the control panel area
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                # Toggle pause/resume when pause button is clicked
                if pause_button_rect.collidepoint(mx, my):
                    paused = not paused
                    if not paused:  # If resuming, clear question and response text
                        question_text = ""
                        gpt_response = ""
                    draw_control_panel()
                # When paused, check if send button is clicked
                if paused and send_button_rect.collidepoint(mx, my):
                    gpt_response = ask_question(question_text)
                    draw_control_panel()
            
            # When paused, capture keyboard events for text input
            if paused and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE:
                    question_text = question_text[:-1]
                elif event.key == pygame.K_RETURN:
                    gpt_response = ask_question(question_text)
                else:
                    question_text += event.unicode
                draw_control_panel()
            
            # Start the sorting if not paused and SPACE key is pressed, only if sorting isn't already running
            if not paused and event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                if sort_thread is None or not sort_thread.is_alive():
                    sort_thread = threading.Thread(target=bubble_sort_with_insights, args=(array,))
                    sort_thread.start()

        draw_control_panel()
        clock.tick(60)
        pygame.display.update()
    
    pygame.quit()

if __name__ == "__main__":
    main()
