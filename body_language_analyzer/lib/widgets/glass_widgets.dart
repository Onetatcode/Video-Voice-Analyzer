import 'package:flutter/material.dart';
import 'dart:ui';

class GlassContainer extends StatelessWidget {
  final Widget child;
  final double blur;
  final double opacity;
  final double borderOpacity;
  final BorderRadius? borderRadius;
  final EdgeInsetsGeometry? padding;
  final EdgeInsetsGeometry? margin;
  final Color? color;
  final List<BoxShadow>? boxShadow;
  final Border? border;

  const GlassContainer({
    super.key,
    required this.child,
    this.blur = 20.0,
    this.opacity = 0.1,
    this.borderOpacity = 0.2,
    this.borderRadius,
    this.padding,
    this.margin,
    this.color,
    this.boxShadow,
    this.border,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    return Container(
      margin: margin,
      decoration: BoxDecoration(
        borderRadius: borderRadius ?? BorderRadius.circular(16),
        boxShadow: boxShadow ??
            [
              BoxShadow(
                color: Colors.black.withOpacity(isDark ? 0.3 : 0.08),
                blurRadius: blur,
                offset: const Offset(0, 4),
                spreadRadius: 0,
              ),
              BoxShadow(
                color: Colors.white.withOpacity(isDark ? 0.05 : 0.5),
                blurRadius: blur / 2,
                offset: const Offset(0, -2),
                spreadRadius: 0,
              ),
            ],
      ),
      child: ClipRRect(
        borderRadius: borderRadius ?? BorderRadius.circular(16),
        child: BackdropFilter(
          filter: ImageFilter.blur(sigmaX: blur, sigmaY: blur),
          child: Container(
            padding: padding,
            decoration: BoxDecoration(
              color: (color ?? theme.colorScheme.surface).withOpacity(opacity),
              borderRadius: borderRadius ?? BorderRadius.circular(16),
              border: border ??
                  Border.all(
                    color: theme.colorScheme.primary.withOpacity(borderOpacity),
                    width: 1,
                  ),
            ),
            child: child,
          ),
        ),
      ),
    );
  }
}

class GlassCard extends StatelessWidget {
  final Widget child;
  final EdgeInsetsGeometry? padding;
  final EdgeInsetsGeometry? margin;
  final VoidCallback? onTap;
  final BorderRadius? borderRadius;

  const GlassCard({
    super.key,
    required this.child,
    this.padding = const EdgeInsets.all(16),
    this.margin,
    this.onTap,
    this.borderRadius,
  });

  @override
  Widget build(BuildContext context) {
    return GlassContainer(
      margin: margin,
      padding: padding,
      borderRadius: borderRadius,
      child: onTap != null
          ? InkWell(
              onTap: onTap,
              borderRadius: borderRadius ?? BorderRadius.circular(16),
              child: child,
            )
          : child,
    );
  }
}

class GlassButton extends StatelessWidget {
  final Widget child;
  final VoidCallback? onPressed;
  final EdgeInsetsGeometry? padding;
  final BorderRadius? borderRadius;
  final Color? backgroundColor;
  final Color? foregroundColor;
  final double blur;
  final double opacity;
  final bool isLoading;
  final Widget? loadingWidget;

  const GlassButton({
    super.key,
    required this.child,
    this.onPressed,
    this.padding = const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
    this.borderRadius,
    this.backgroundColor,
    this.foregroundColor,
    this.blur = 20.0,
    this.opacity = 0.15,
    this.isLoading = false,
    this.loadingWidget,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDisabled = onPressed == null || isLoading;

    return GlassContainer(
      blur: blur,
      opacity: isDisabled ? opacity * 0.5 : opacity,
      borderRadius: borderRadius ?? BorderRadius.circular(12),
      color: backgroundColor ?? theme.colorScheme.primary,
      padding: padding,
      child: InkWell(
        onTap: isDisabled ? null : onPressed,
        borderRadius: borderRadius ?? BorderRadius.circular(12),
        child: Center(
          child: isLoading
              ? (loadingWidget ??
                  SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      valueColor: AlwaysStoppedAnimation<Color>(
                        foregroundColor ?? theme.colorScheme.onPrimary,
                      ),
                    ),
                  ))
              : DefaultTextStyle(
                  style: TextStyle(
                    color: foregroundColor ?? theme.colorScheme.onPrimary,
                    fontWeight: FontWeight.w600,
                    fontSize: 14,
                    letterSpacing: 0.5,
                  ),
                  child: child,
                ),
        ),
      ),
    );
  }
}

class GlassAppBar extends StatelessWidget implements PreferredSizeWidget {
  final Widget? title;
  final Widget? leading;
  final List<Widget>? actions;
  final double height;
  final double blur;
  final double opacity;
  final Color? backgroundColor;
  final PreferredSizeWidget? bottom;
  final bool centerTitle;

  const GlassAppBar({
    super.key,
    this.title,
    this.leading,
    this.actions,
    this.height = kToolbarHeight,
    this.blur = 20.0,
    this.opacity = 0.1,
    this.backgroundColor,
    this.bottom,
    this.centerTitle = true,
  });

  @override
  Size get preferredSize => Size.fromHeight(height + (bottom?.preferredSize.height ?? 0));

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return AppBar(
      title: title,
      leading: leading,
      actions: actions,
      centerTitle: centerTitle,
      bottom: bottom,
      elevation: 0,
      scrolledUnderElevation: 0,
      backgroundColor: Colors.transparent,
      foregroundColor: theme.colorScheme.onSurface,
      flexibleSpace: ClipRect(
        child: BackdropFilter(
          filter: ImageFilter.blur(sigmaX: blur, sigmaY: blur),
          child: Container(
            color: (backgroundColor ?? theme.colorScheme.surface).withOpacity(opacity),
          ),
        ),
      ),
    );
  }
}

class GlassBottomNav extends StatelessWidget {
  final int currentIndex;
  final ValueChanged<int> onTap;
  final List<GlassBottomNavItem> items;
  final double height;
  final double blur;
  final double opacity;

  const GlassBottomNav({
    super.key,
    required this.currentIndex,
    required this.onTap,
    required this.items,
    this.height = 80,
    this.blur = 20.0,
    this.opacity = 0.15,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return GlassContainer(
      blur: blur,
      opacity: opacity,
      borderRadius: const BorderRadius.vertical(top: Radius.circular(20)),
      margin: EdgeInsets.zero,
      padding: EdgeInsets.zero,
      child: SizedBox(
        height: height,
        child: NavigationBar(
          selectedIndex: currentIndex,
          onDestinationSelected: onTap,
          indicatorColor: theme.colorScheme.primary.withOpacity(0.15),
          backgroundColor: Colors.transparent,
          elevation: 0,
          labelBehavior: NavigationDestinationLabelBehavior.alwaysShow,
          animationDuration: const Duration(milliseconds: 300),
          destinations: items.map((item) {
            return NavigationDestination(
              icon: Icon(item.icon, size: 24),
              selectedIcon: Icon(item.selectedIcon ?? item.icon, size: 24),
              label: item.label,
              tooltip: item.tooltip,
            );
          }).toList(),
        ),
      ),
    );
  }
}

class GlassBottomNavItem {
  final IconData icon;
  final IconData? selectedIcon;
  final String label;
  final String? tooltip;

  const GlassBottomNavItem({
    required this.icon,
    this.selectedIcon,
    required this.label,
    this.tooltip,
  });
}

class GlassTextField extends StatelessWidget {
  final TextEditingController? controller;
  final String? labelText;
  final String? hintText;
  final String? errorText;
  final TextInputType? keyboardType;
  final bool obscureText;
  final Widget? prefixIcon;
  final Widget? suffixIcon;
  final ValueChanged<String>? onChanged;
  final ValueChanged<String>? onSubmitted;
  final FormFieldValidator<String>? validator;
  final int? maxLines;
  final int? minLines;
  final TextCapitalization textCapitalization;
  final bool enabled;
  final double blur;
  final double opacity;

  const GlassTextField({
    super.key,
    this.controller,
    this.labelText,
    this.hintText,
    this.errorText,
    this.keyboardType,
    this.obscureText = false,
    this.prefixIcon,
    this.suffixIcon,
    this.onChanged,
    this.onSubmitted,
    this.validator,
    this.maxLines = 1,
    this.minLines,
    this.textCapitalization = TextCapitalization.none,
    this.enabled = true,
    this.blur = 10.0,
    this.opacity = 0.08,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return GlassContainer(
      blur: blur,
      opacity: opacity,
      borderRadius: BorderRadius.circular(12),
      padding: EdgeInsets.zero,
      child: TextFormField(
        controller: controller,
        obscureText: obscureText,
        keyboardType: keyboardType,
        onChanged: onChanged,
        onFieldSubmitted: onSubmitted,
        validator: validator,
        maxLines: maxLines,
        minLines: minLines,
        textCapitalization: textCapitalization,
        enabled: enabled,
        style: theme.textTheme.bodyLarge,
        decoration: InputDecoration(
          labelText: labelText,
          hintText: hintText,
          errorText: errorText,
          prefixIcon: prefixIcon,
          suffixIcon: suffixIcon,
          border: InputBorder.none,
          contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
          labelStyle: TextStyle(color: theme.colorScheme.onSurface.withOpacity(0.7)),
          hintStyle: TextStyle(color: theme.colorScheme.onSurface.withOpacity(0.5)),
          errorStyle: TextStyle(color: theme.colorScheme.error),
        ),
      ),
    );
  }
}

class GlassProgressIndicator extends StatelessWidget {
  final double value;
  final double height;
  final Color? color;
  final Color? backgroundColor;
  final BorderRadius? borderRadius;

  const GlassProgressIndicator({
    super.key,
    this.value = 0.0,
    this.height = 8,
    this.color,
    this.backgroundColor,
    this.borderRadius,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return GlassContainer(
      blur: 5,
      opacity: 0.05,
      borderRadius: borderRadius ?? BorderRadius.circular(height / 2),
      padding: EdgeInsets.zero,
      child: LinearProgressIndicator(
        value: value,
        minHeight: height,
        backgroundColor: backgroundColor ?? theme.colorScheme.primary.withOpacity(0.2),
        valueColor: AlwaysStoppedAnimation<Color>(color ?? theme.colorScheme.primary),
        borderRadius: borderRadius ?? BorderRadius.circular(height / 2),
      ),
    );
  }
}

class GlassSnackBar extends SnackBar {
  GlassSnackBar({
    super.key,
    required super.content,
    super.duration = const Duration(seconds: 3),
    super.action,
    double blur = 20.0,
    double opacity = 0.15,
  }) : super(
          behavior: SnackBarBehavior.floating,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          backgroundColor: Colors.transparent,
          elevation: 0,
          padding: EdgeInsets.zero,
        );
}